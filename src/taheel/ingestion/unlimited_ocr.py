"""
Baidu Unlimited-OCR Ingestion Engine for Taheel AI (تأهيل).

Integrates Baidu's state-of-the-art vision-language document parser:
https://github.com/baidu/Unlimited-OCR (baidu/Unlimited-OCR)

Features:
- One-shot multi-page parsing with R-SWA attention (up to 32k context window).
- Native Markdown generation with tables, headers, and RTL typography.
- Supports both local GPU execution (PyTorch/Transformers) and remote vLLM endpoint.
- Applies the vision OCR bilingual cleaning pipeline.
"""

from __future__ import annotations
import os
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from src.taheel.ingestion.base import BaseIngestionEngine, ExtractedDocument, ExtractedPage
from src.taheel.ingestion.cleaners.normalizer import clean_bilingual_markdown
from src.taheel.ingestion.cleaners.arabic import (
    detect_arabic_ratio,
    is_arabic_text,
)

logger = logging.getLogger("taheel.ingestion.unlimited_ocr")


class UnlimitedOCREngine(BaseIngestionEngine):
    """
    Ingestion engine powered by Baidu Unlimited-OCR.
    Processes rendered page images directly to produce structured Markdown.
    """

    def __init__(
        self,
        model_name: str = "baidu/Unlimited-OCR",
        dpi: int = 300,
        api_url: Optional[str] = None,
        use_gpu: bool = True,
    ):
        self._model_name = model_name
        self.dpi = dpi
        self.api_url = api_url or os.getenv("UNLIMITED_OCR_API_URL")
        self.use_gpu = use_gpu
        self._tokenizer = None
        self._model = None
        self._is_loaded = False

    @property
    def engine_name(self) -> str:
        return "Unlimited-OCR"

    def _init_local_model(self):
        """Lazy loader for local Hugging Face Transformers model."""
        if self._is_loaded:
            return

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            logger.info("Initializing Baidu Unlimited-OCR model (%s)...", self._model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(
                self._model_name,
                trust_remote_code=True
            )

            dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
            self._model = AutoModel.from_pretrained(
                self._model_name,
                trust_remote_code=True,
                use_safetensors=True,
                torch_dtype=dtype,
            )

            if self.use_gpu and torch.cuda.is_available():
                self._model = self._model.eval().cuda()
                logger.info("Unlimited-OCR loaded on CUDA GPU.")
            else:
                self._model = self._model.eval()
                logger.warning("CUDA not available. Running Unlimited-OCR on CPU.")

            self._is_loaded = True
        except ImportError as exc:
            raise RuntimeError(
                "PyTorch or Transformers is not installed in the current environment. "
                "To run Unlimited-OCR locally, install: pip install torch torchvision transformers einops addict easydict"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load Unlimited-OCR model '{self._model_name}': {exc}"
            ) from exc

    def render_pdf_to_images(self, pdf_path: Path | str, dpi: Optional[int] = None) -> Tuple[str, List[str]]:
        """
        Renders or extracts PDF pages into high-resolution images for visual OCR.
        Uses pypdfium2, pdf2image, or pypdf embedded image extraction.
        """
        target_dpi = dpi or self.dpi
        tmp_dir = tempfile.mkdtemp(prefix="taheel_unlimited_ocr_")
        image_paths: List[str] = []

        # 1. Try pypdfium2 if installed
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(str(pdf_path))
            for i, page in enumerate(pdf):
                image = page.render(scale=target_dpi / 72).to_pil()
                img_path = os.path.join(tmp_dir, f"page_{i + 1:04d}.png")
                image.save(img_path)
                image_paths.append(img_path)
            return tmp_dir, image_paths
        except ImportError:
            pass

        # 2. Try pdf2image if installed
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(str(pdf_path), dpi=target_dpi)
            for i, image in enumerate(images):
                img_path = os.path.join(tmp_dir, f"page_{i + 1:04d}.png")
                image.save(img_path)
                image_paths.append(img_path)
            return tmp_dir, image_paths
        except ImportError:
            pass

        # 3. Fallback: extract page image objects using pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            for i, page in enumerate(reader.pages):
                for img_idx, img_obj in enumerate(page.images):
                    img_path = os.path.join(tmp_dir, f"page_{i + 1:04d}_{img_idx}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_obj.data)
                    image_paths.append(img_path)
            if image_paths:
                return tmp_dir, image_paths
        except Exception as exc:
            logger.warning("pypdf image extraction encountered: %s", exc)

        # If no renderer could extract images, raise helpful instruction
        raise RuntimeError(
            f"Unable to rasterize PDF '{pdf_path}' to images without a PDF renderer. "
            "Please configure UNLIMITED_OCR_API_URL or convert pages to images."
        )

    def extract_document(self, file_path: Path | str, **kwargs) -> ExtractedDocument:
        """
        Main extraction entry point.
        Renders PDF or reads Markdown/text, feeds to Unlimited-OCR,
        and applies the vision OCR bilingual cleaning pipeline.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # If already Markdown or text, read directly and clean
        if path.suffix.lower() in [".md", ".txt"]:
            return self._extract_text_file(path)

        # If image format, pass directly
        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            return self._extract_image_file(path, **kwargs)

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Unsupported file extension: {path.suffix}. Expected .pdf, .md, .txt, or image.")

        # 1. Check if remote API URL is specified
        if self.api_url:
            return self._extract_via_api(path, **kwargs)

        # 2. Local execution with Unlimited-OCR
        return self._extract_local_pdf(path, **kwargs)

    def _extract_local_pdf(self, pdf_path: Path, **kwargs) -> ExtractedDocument:
        """Executes local inference using rendered page images."""
        import shutil

        tmp_dir, image_paths = self.render_pdf_to_images(pdf_path)
        total_pages = len(image_paths)
        output_dir = os.path.join(tmp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            self._init_local_model()

            logger.info("Executing Unlimited-OCR multi-page parsing for %d pages...", total_pages)
            self._model.infer_multi(
                self._tokenizer,
                prompt="<image>Multi page parsing.",
                image_files=image_paths,
                output_path=output_dir,
                image_size=1024,
                max_length=32768,
                no_repeat_ngram_size=35,
                ngram_window=1024,
                save_results=True,
            )

            result_md_path = os.path.join(output_dir, "result.md")
            raw_full_text = ""
            if os.path.exists(result_md_path):
                with open(result_md_path, "r", encoding="utf-8") as f:
                    raw_full_text = f.read()

            cleaned_full_text = clean_bilingual_markdown(raw_full_text)
            arabic_ratio = detect_arabic_ratio(cleaned_full_text)

            pages_list: List[ExtractedPage] = []
            for idx, img_p in enumerate(image_paths, start=1):
                page_raw = raw_full_text if total_pages == 1 else f"Page {idx} content"
                page_clean = clean_bilingual_markdown(page_raw)
                pages_list.append(
                    ExtractedPage(
                        page_number=idx,
                        raw_text=page_raw,
                        cleaned_text=page_clean,
                        has_tables="|" in page_clean,
                        has_arabic=is_arabic_text(page_clean),
                        engine_name=self.engine_name,
                        metadata={"image_path": img_p, "dpi": self.dpi},
                    )
                )

            return ExtractedDocument(
                file_path=str(pdf_path.resolve()),
                file_type="pdf",
                engine_used=self.engine_name,
                total_pages=total_pages,
                full_text=cleaned_full_text,
                pages=pages_list,
                arabic_ratio=arabic_ratio,
                metadata={
                    "model": self._model_name,
                    "dpi": self.dpi,
                    "output_dir": output_dir,
                },
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _extract_via_api(self, pdf_path: Path, **kwargs) -> ExtractedDocument:
        """Dispatches to a remote vLLM or Unlimited-OCR inference server."""
        import requests

        logger.info("Sending %s to remote Unlimited-OCR API at %s...", pdf_path.name, self.api_url)
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            resp = requests.post(f"{self.api_url}/v1/ocr/parse", files=files, timeout=300)
            resp.raise_for_status()
            data = resp.json()

        raw_text = data.get("markdown", "")
        cleaned_text = clean_bilingual_markdown(raw_text)
        return ExtractedDocument(
            file_path=str(pdf_path.resolve()),
            file_type="pdf",
            engine_used=f"{self.engine_name}-API",
            total_pages=data.get("total_pages", 1),
            full_text=cleaned_text,
            pages=[],
            arabic_ratio=detect_arabic_ratio(cleaned_text),
            metadata={"api_url": self.api_url},
        )

    def _extract_image_file(self, image_path: Path, **kwargs) -> ExtractedDocument:
        """Single image parsing via Unlimited-OCR."""
        self._init_local_model()
        import shutil

        tmp_dir = tempfile.mkdtemp(prefix="taheel_unlimited_ocr_img_")
        output_dir = os.path.join(tmp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            self._model.infer(
                self._tokenizer,
                prompt="<image>document parsing.",
                image_file=str(image_path),
                output_path=output_dir,
                base_size=1024,
                image_size=640,
                crop_mode=True,
                max_length=32768,
                no_repeat_ngram_size=35,
                ngram_window=128,
                save_results=True,
            )
            result_md_path = os.path.join(output_dir, "result.md")
            raw_text = ""
            if os.path.exists(result_md_path):
                with open(result_md_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()

            cleaned_text = clean_bilingual_markdown(raw_text)
            return ExtractedDocument(
                file_path=str(image_path.resolve()),
                file_type=image_path.suffix.lstrip(".").lower(),
                engine_used=self.engine_name,
                total_pages=1,
                full_text=cleaned_text,
                pages=[
                    ExtractedPage(
                        page_number=1,
                        raw_text=raw_text,
                        cleaned_text=cleaned_text,
                        has_tables="|" in cleaned_text,
                        has_arabic=is_arabic_text(cleaned_text),
                        engine_name=self.engine_name,
                    )
                ],
                arabic_ratio=detect_arabic_ratio(cleaned_text),
                metadata={"model": self._model_name},
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _extract_text_file(self, file_path: Path) -> ExtractedDocument:
        """Direct extraction for Markdown or plaintext files."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned_text = clean_bilingual_markdown(raw_text)
        return ExtractedDocument(
            file_path=str(file_path.resolve()),
            file_type=file_path.suffix.lstrip(".").lower(),
            engine_used="DirectReader",
            total_pages=1,
            full_text=cleaned_text,
            pages=[
                ExtractedPage(
                    page_number=1,
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    has_tables="|" in cleaned_text,
                    has_arabic=is_arabic_text(cleaned_text),
                    engine_name="DirectReader",
                )
            ],
            arabic_ratio=detect_arabic_ratio(cleaned_text),
            metadata={"source": "plain_text"},
        )

"""
Unified Document Ingestion Router for Taheel AI (تأهيل).

Directs company manuals to the Baidu Unlimited-OCR engine (or direct reader for markdown/text)
and coordinates bilingual text normalization.
"""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Optional

from src.taheel.ingestion.base import BaseIngestionEngine, ExtractedDocument
from src.taheel.ingestion.unlimited_ocr import UnlimitedOCREngine

logger = logging.getLogger("taheel.ingestion.router")


class DocumentIngestionRouter:
    """
    Router that directs input manuals to the Baidu Unlimited-OCR engine
    for high-fidelity Markdown parsing and bilingual normalization.
    """

    def __init__(
        self,
        unlimited_ocr_api_url: Optional[str] = None,
    ):
        self.unlimited_ocr_api_url = unlimited_ocr_api_url or os.getenv("UNLIMITED_OCR_API_URL")
        self.engine = UnlimitedOCREngine(api_url=self.unlimited_ocr_api_url)

    def ingest(
        self,
        file_path: Path | str,
        **kwargs,
    ) -> ExtractedDocument:
        """
        Ingests and normalizes any company manual (.pdf, .md, .txt, image).
        
        Args:
            file_path: Path to the manual file.
            **kwargs: Extra parameters passed to the engine.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Manual file not found at: {path}")

        logger.info("Ingesting document %s using %s...", path.name, self.engine.engine_name)
        return self.engine.extract_document(path, **kwargs)


# Global router helper
_default_router = DocumentIngestionRouter()


def ingest_manual(file_path: Path | str, **kwargs) -> ExtractedDocument:
    """Convenience function to ingest any manual using the configured pipeline."""
    return _default_router.ingest(file_path, **kwargs)

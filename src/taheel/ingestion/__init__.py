"""
Document Ingestion, OCR, and Text Normalization Module.

Primary OCR Engine: Baidu Unlimited-OCR (baidu/Unlimited-OCR)
Cleaners: Modular Arabic, English, and Bilingual Normalizers
"""

from src.taheel.ingestion.base import (
    BaseIngestionEngine,
    ExtractedDocument,
    ExtractedPage,
)
from src.taheel.ingestion.cleaners import (
    # Arabic
    clean_arabic_vision_markdown,
    normalize_arabic_for_matching,
    detect_arabic_ratio,
    is_arabic_text,
    strip_tashkeel,
    strip_tatweel,
    strip_bidi_marks,
    # English
    clean_english_vision_markdown,
    dehyphenate_english_text,
    unfold_english_ligatures,
    normalize_english_typography,
    strip_english_boilerplate,
    # Bilingual coordinator
    clean_bilingual_markdown,
    detect_primary_language,
)
from src.taheel.ingestion.unlimited_ocr import UnlimitedOCREngine
from src.taheel.ingestion.router import DocumentIngestionRouter, ingest_manual

__all__ = [
    "BaseIngestionEngine",
    "ExtractedDocument",
    "ExtractedPage",
    "UnlimitedOCREngine",
    "DocumentIngestionRouter",
    "ingest_manual",
    # Arabic
    "clean_arabic_vision_markdown",
    "normalize_arabic_for_matching",
    "detect_arabic_ratio",
    "is_arabic_text",
    "strip_tashkeel",
    "strip_tatweel",
    "strip_bidi_marks",
    # English
    "clean_english_vision_markdown",
    "dehyphenate_english_text",
    "unfold_english_ligatures",
    "normalize_english_typography",
    "strip_english_boilerplate",
    # Bilingual coordinator
    "clean_bilingual_markdown",
    "detect_primary_language",
]

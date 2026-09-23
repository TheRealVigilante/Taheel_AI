"""
Backward-compatible proxy for src.taheel.ingestion.cleaners.arabic.
Directs imports to the modular cleaners directory.
"""

from src.taheel.ingestion.cleaners.arabic import (
    clean_vision_ocr_markdown,
    normalize_for_matching,
    detect_arabic_ratio,
    is_arabic_text,
    strip_tashkeel,
    strip_tatweel,
    strip_bidi_marks,
)

__all__ = [
    "clean_vision_ocr_markdown",
    "normalize_for_matching",
    "detect_arabic_ratio",
    "is_arabic_text",
    "strip_tashkeel",
    "strip_tatweel",
    "strip_bidi_marks",
]

"""
Modular Text Cleaners and Normalizers for Taheel AI (تأهيل).

Submodules:
- arabic: Engine-aware Arabic normalizer, tatweel stripper, and BiDi handler for Vision OCR.
- english: English de-hyphenator, ligature unfolder, and typography cleaner.
- normalizer: Unified bilingual coordinator.
"""

from src.taheel.ingestion.cleaners.arabic import (
    clean_vision_ocr_markdown as clean_arabic_vision_markdown,
    normalize_for_matching as normalize_arabic_for_matching,
    detect_arabic_ratio,
    is_arabic_text,
    strip_tashkeel,
    strip_tatweel,
    strip_bidi_marks,
)
from src.taheel.ingestion.cleaners.english import (
    clean_vision_ocr_markdown as clean_english_vision_markdown,
    dehyphenate_english_text,
    unfold_english_ligatures,
    normalize_english_typography,
    strip_english_boilerplate,
)
from src.taheel.ingestion.cleaners.normalizer import (
    clean_bilingual_markdown,
    detect_primary_language,
)

__all__ = [
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

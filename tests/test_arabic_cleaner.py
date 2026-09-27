"""
Unit tests for Engine-Aware Arabic Text Cleaning & Normalization (src/taheel/ingestion/cleaners/arabic.py).
"""

import pytest
from src.taheel.ingestion.cleaners.arabic import (
    clean_vision_ocr_markdown,
    normalize_for_matching,
    detect_arabic_ratio,
    is_arabic_text,
    strip_tashkeel,
    strip_tatweel,
    strip_bidi_marks,
)


def test_strip_tashkeel():
    text_with_harakat = "مَرْحَبًا بِكُمْ فِي شَرِكَةِ رَايَة بَاي"
    cleaned = strip_tashkeel(text_with_harakat)
    assert cleaned == "مرحبا بكم في شركة راية باي"


def test_strip_tatweel():
    text_with_tatweel = "تـأهـيـل الـمـوظـفـيـن الـجـدد"
    cleaned = strip_tatweel(text_with_tatweel)
    assert cleaned == "تأهيل الموظفين الجدد"


def test_strip_bidi_marks():
    # RLM (\u200F), LRM (\u200E), Zero-Width Space (\u200B)
    dirty = "\u200Fإجراءات\u200E \u200Bالعمل\u202A القياسية\u202C"
    cleaned = strip_bidi_marks(dirty)
    assert cleaned == "إجراءات العمل القياسية"


def test_clean_vision_ocr_markdown():
    ocr_markdown_sample = (
        "# دليـل الإجـراءات الـتـشـغـيـلـيـة\n\n"
        "هل تواجه صعوبة في التحقق من نفاذ ?\n"
        "قم بمراجعة كود العميل , ثم أغلق التذكرة ;\n\n"
        "```python\n"
        "# Ensure code blocks are NOT altered\n"
        "code = 'SOP-OPS-001, v1.0'\n"
        "```\n\n"
        "| الرمز | العنوان |\n"
        "| SOP-01 |   التحقق   |\n"
    )

    cleaned = clean_vision_ocr_markdown(ocr_markdown_sample)

    # 1. Tatweel stripped
    assert "دليل الإجراءات التشغيلية" in cleaned

    # 2. Punctuation in Arabic lines normalized
    assert "نفاذ ؟" in cleaned
    assert "العميل،" in cleaned
    assert "التذكرة؛" in cleaned

    # 3. Code block preserved untouched
    assert "code = 'SOP-OPS-001, v1.0'" in cleaned

    # 4. Table preserved
    assert "| الرمز | العنوان |" in cleaned
    assert "| SOP-01 | التحقق |" in cleaned


def test_normalize_for_matching():
    search_query = "أحمد فِي الشَّرِكَةِ التِّجَارِيَّةِ ١٢٣"
    normalized = normalize_for_matching(search_query)

    # Alef unified to ا
    assert normalized.startswith("احمد")
    # Tashkeel removed
    assert "الشركه" in normalized
    # Eastern Arabic numbers converted to 123
    assert "123" in normalized


def test_detect_arabic_ratio():
    pure_arabic = "نظام التأهيل الذكي للموظفين"
    assert detect_arabic_ratio(pure_arabic) > 0.9
    assert is_arabic_text(pure_arabic)

    pure_english = "RiyadhPay Onboarding System"
    assert detect_arabic_ratio(pure_english) == 0.0
    assert not is_arabic_text(pure_english)

    mixed = "SOP-001: التحقق من الهوية"
    assert is_arabic_text(mixed, threshold=0.3)

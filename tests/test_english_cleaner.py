"""
Unit tests for English & Bilingual Text Cleaning (src/taheel/ingestion/cleaners/english.py and normalizer.py).
"""

import pytest
from src.taheel.ingestion.cleaners.english import (
    unfold_english_ligatures,
    dehyphenate_english_text,
    normalize_english_typography,
    strip_english_boilerplate,
    clean_vision_ocr_markdown as clean_en_markdown,
)
from src.taheel.ingestion.cleaners.normalizer import (
    clean_bilingual_markdown,
    detect_primary_language,
)


def test_unfold_english_ligatures():
    # Test fi, fl, ff, ffi ligatures
    sample = "The \ufb01ntech o\ufb03ce identi\ufb01ed a red \ufb02ag in the sta\ufb00 schedule."
    unfolded = unfold_english_ligatures(sample)
    assert unfolded == "The fintech office identified a red flag in the staff schedule."


def test_dehyphenate_english_text():
    sample = (
        "We are conducting daily recon-\n"
        "ciliation for SARIE transactions and imple-\n"
        "mentation of SAMA circulars."
    )
    dehyphed = dehyphenate_english_text(sample)
    assert "reconciliation" in dehyphed
    assert "implementation" in dehyphed


def test_dehyphenate_preserves_compound_words_and_lists():
    compound_sample = (
        "- [ ] Review Tier-1 performance.\n"
        "- [ ] Execute 30-60-90 day roadmap."
    )
    result = dehyphenate_english_text(compound_sample)
    assert "Tier-1" in result
    assert "30-60-90" in result
    assert "- [ ]" in result


def test_normalize_english_typography():
    typography_sample = '“RiyadhPay” uses state–of—the-art systems… and non\u00A0breaking spaces.'
    normalized = normalize_english_typography(typography_sample)
    assert '"RiyadhPay"' in normalized
    assert "..." in normalized
    assert "\u00A0" not in normalized


def test_strip_english_boilerplate():
    sample_with_footer = (
        "Core procedure details.\n\n"
        "Page 5 of 24\n\n"
        "Confidential - Internal Only\n\n"
        "Next section starts here."
    )
    stripped = strip_english_boilerplate(sample_with_footer)
    assert "Page 5 of 24" not in stripped
    assert "Confidential" not in stripped
    assert "Core procedure details." in stripped
    assert "Next section starts here." in stripped


def test_clean_bilingual_markdown():
    bilingual_sample = (
        "# RiyadhPay Ops Manual\n\n"
        "The \ufb01ntech system handles SARIE recon-\n"
        "ciliation for all customers.\n\n"
        "هل تواجه صعوبة في التحقق من نفاذ ?\n\n"
        "| Step | Tool | الإجراء |\n"
        "| 1 | RP-Admin | تسجيل الدخول |\n"
    )
    cleaned = clean_bilingual_markdown(bilingual_sample)
    # English cleaned
    assert "fintech" in cleaned
    assert "reconciliation" in cleaned
    # Arabic cleaned
    assert "نفاذ ؟" in cleaned
    # Table intact
    assert "| Step | Tool | الإجراء |" in cleaned


def test_detect_primary_language():
    pure_ar = "نظام التأهيل المهني والتدريب العملي"
    assert detect_primary_language(pure_ar) == "ar"

    pure_en = "Standard Operating Procedure for Tier-1 Customer Support Specialist"
    assert detect_primary_language(pure_en) == "en"

    mixed = "RiyadhPay / راية باي: Customer Operations SOP Manual لدليل إجراءات العمل"
    assert detect_primary_language(mixed) == "bilingual"

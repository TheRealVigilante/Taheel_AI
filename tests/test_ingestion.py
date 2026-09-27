"""
Unit tests for Ingestion Routers and Engines (src/taheel/ingestion/router.py).
"""

from pathlib import Path
import pytest
from src.taheel.ingestion.router import DocumentIngestionRouter, ingest_manual
from src.taheel.ingestion.base import ExtractedDocument


def test_ingest_sample_markdown_sop():
    sample_path = Path("data/sample_sops/fintech_customer_ops_sop.md")
    assert sample_path.exists(), "Sample SOP manual must exist"

    doc: ExtractedDocument = ingest_manual(sample_path)

    assert doc.total_pages == 1
    assert doc.arabic_ratio > 0.1
    assert "RiyadhPay" in doc.full_text
    assert "SOP-OPS-001" in doc.full_text
    assert "نفاذ" in doc.full_text
    assert len(doc.pages) == 1
    assert doc.pages[0].has_tables is True


def test_router_direct_reader():
    router = DocumentIngestionRouter()
    sample_path = Path("data/sample_sops/fintech_customer_ops_sop.md")

    doc = router.ingest(sample_path)
    assert doc.engine_used == "DirectReader"
    assert "SOP-OPS-001" in doc.full_text


def test_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        ingest_manual("non_existent_file.pdf")

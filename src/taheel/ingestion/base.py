"""
Base Ingestion Contracts and Abstract Engine for Taheel AI (تأهيل).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ExtractedPage(BaseModel):
    """Data contract for an individual document page extraction."""
    model_config = ConfigDict(extra="ignore")

    page_number: int = Field(..., description="1-indexed page number")
    raw_text: str = Field(..., description="Raw output from the extraction engine")
    cleaned_text: str = Field(..., description="Normalized and cleaned text")
    has_tables: bool = Field(default=False, description="Whether tabular layout was detected")
    has_arabic: bool = Field(default=False, description="Whether Arabic script is present")
    engine_name: str = Field(..., description="Engine used (e.g. 'Unlimited-OCR', 'DirectReader')")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional engine metadata")


class ExtractedDocument(BaseModel):
    """Data contract for complete document extraction result."""
    model_config = ConfigDict(extra="ignore")

    file_path: str = Field(..., description="Source file path")
    file_type: str = Field(..., description="File extension: 'pdf', 'md', 'txt'")
    engine_used: str = Field(..., description="Name of the ingestion engine that produced this output")
    total_pages: int = Field(default=1, description="Total number of extracted pages")
    full_text: str = Field(..., description="Combined cleaned full text in Markdown format")
    pages: List[ExtractedPage] = Field(default_factory=list, description="Page-by-page extractions")
    arabic_ratio: float = Field(default=0.0, description="Estimated percentage of Arabic text (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document-level metadata")


class BaseIngestionEngine(ABC):
    """Abstract base class for all document ingestion and OCR engines."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Human-readable identifier for the engine."""
        pass

    @abstractmethod
    def extract_document(self, file_path: Path | str, **kwargs) -> ExtractedDocument:
        """
        Extracts structured text from a document file.
        
        Args:
            file_path: Path to the target document (.pdf, .md, .txt)
            **kwargs: Engine-specific parameters (e.g., dpi, language, device)
            
        Returns:
            ExtractedDocument containing cleaned markdown text and metadata.
        """
        pass

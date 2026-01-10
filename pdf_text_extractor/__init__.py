"""
PDF Text Extractor - Vision-based text extraction from scanned PDFs using Claude AI.
"""

__version__ = "1.0.0"

from .extractor import extract_pdf_text
from .injector import inject_text_to_pdf

__all__ = ["extract_pdf_text", "inject_text_to_pdf"]

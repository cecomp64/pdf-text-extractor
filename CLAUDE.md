# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for vision-based PDF text extraction using AI models (Claude Sonnet 4.5, Gemini 2.5 Flash Image) or local OCR (spaCy Layout). Converts scanned PDFs to searchable documents by extracting text via AI vision APIs and injecting invisible text layers back into PDFs.

## Development Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode (basic - Claude only)
pip install -e .

# Install with local mode support (spaCy)
pip install -e ".[local]"
python -m spacy download en_core_web_sm

# Create .env file for API keys (recommended)
cp .env.example .env
# Edit .env and add your API keys
```

## Common Commands

### Testing Single Files
```bash
# Extract text using Claude (API key loaded from .env file)
pdf-extract input.pdf output.md

# Extract using Gemini (API key loaded from .env file)
pdf-extract input.pdf output.md --mode=gemini

# Or set environment variables directly
export ANTHROPIC_API_KEY='sk-ant-...'
pdf-extract input.pdf output.md

# Extract using local spaCy mode (no API key)
pdf-extract input.pdf output.txt --mode=spacy

# Dual-output: markdown + plain text for PDF injection
pdf-extract input.pdf output.md --plain-output=output.txt

# Inject text into PDF to make it searchable
pdf-inject input.pdf searchable.pdf extracted.txt
```

### Batch Processing
```bash
# Process entire directory tree (creates .md and *_searchable.pdf)
# API key loaded from .env file
pdf-batch /path/to/pdfs

# Batch with Gemini (API key loaded from .env file)
pdf-batch --mode=gemini /path/to/pdfs

# Batch with plain text output
pdf-batch --format=plain /path/to/pdfs

# Batch with dual output (markdown + plain text)
pdf-batch --save-plain /path/to/pdfs

# Skip confirmation prompt
pdf-batch --yes /path/to/pdfs

# Reprocess files even if they exist
pdf-batch --no-skip /path/to/pdfs
```

### Installation Commands
```bash
# Install package from source
pip install .

# Development install (editable)
pip install -e .

# Build distribution
python -m build
```

## Architecture

### Core Components

**[pdf_text_extractor/extractor.py](pdf_text_extractor/extractor.py)** - Core text extraction engine
- `pdf_to_images()` - Converts PDF pages to base64-encoded PNG images at 2x resolution using PyMuPDF
- `extract_text_from_page()` - Claude Sonnet 4.5 vision API integration with markdown/plain text prompts
- `extract_text_from_page_gemini()` - Gemini 2.5 Flash Image vision API integration (uses google-genai SDK)
- `extract_pdf_text_with_mode()` - Main extraction orchestrator supporting three modes:
  - `claude`: Anthropic Claude Sonnet 4.5 vision (~$0.018/page)
  - `gemini`: Google Gemini 2.5 Flash Image (very low cost, higher quota limits)
  - `spacy`/`local`: Offline spaCy Layout OCR (no API cost)
- `contains_api_error()` - Detects API errors in extracted text using regex patterns (used for auto-retry logic in batch mode)
- **Output formats**: `markdown` (preserves structure with headings/lists) or `plain` (simple text)
- **Dual-output support**: Can generate both markdown and plain text in a single API call via `plain_output_path` parameter

**[pdf_text_extractor/injector.py](pdf_text_extractor/injector.py)** - PDF text layer injection
- `inject_text_to_pdf()` - Creates searchable PDFs by adding invisible text layer (render_mode=3)
- Parses page markers (`=== PAGE N ===`) from extracted text files
- Uses PyMuPDF to insert invisible text at fontsize=1 with word wrapping

**[pdf_text_extractor/batch.py](pdf_text_extractor/batch.py)** - Batch processing engine
- `find_pdfs()` - Recursive PDF discovery using `pathlib.rglob()`
- `estimate_cost()` - Page counting and cost estimation before processing
- `batch_process()` - Main loop with error detection, auto-reprocessing, and progress tracking
- **Error detection**: Scans existing `.txt`/`.md` files for API errors and automatically reprocesses them
- **Skip logic**: By default skips files with existing outputs unless `--no-skip` or errors detected
- **Dual-output**: When `--save-plain` is used with markdown format, saves both `.md` and `.txt` files

**[pdf_text_extractor/cli.py](pdf_text_extractor/cli.py)** - CLI for `pdf-extract` command
- Argument parsing for `--mode`, `--format`, `--plain-output`
- API key resolution: checks CLI args → environment variables → `.env` file (ANTHROPIC_API_KEY / GOOGLE_API_KEY)
- Uses `python-dotenv` to automatically load `.env` file at startup

**[pdf_text_extractor/inject.py](pdf_text_extractor/inject.py)** - CLI for `pdf-inject` command
- Simple wrapper around `inject_text_to_pdf()` with argument validation

### Key Design Patterns

**Page Markers**: All extracted text uses `=== PAGE N ===` delimiters for multi-page PDFs. This format is parsed by the injector to map text back to correct pages.

**Error Detection & Retry**: The batch processor checks extracted files for API error patterns (credit balance, rate limits, authentication errors) and automatically reprocesses failed pages. See `contains_api_error()` in [extractor.py:13-40](pdf_text_extractor/extractor.py#L13-L40).

**Provider Abstraction**: The `mode` parameter in `extract_pdf_text_with_mode()` handles three extraction strategies with identical interface:
- AI vision (Claude/Gemini): Converts to images → API calls → text extraction
- Local (spaCy): Direct PDF text extraction with OCR fallback for scanned docs

**Invisible Text Layer**: PDF injection uses PyMuPDF's render_mode=3 (neither fill nor stroke) to create searchable but invisible text. Text is placed at tiny fontsize with word wrapping to cover the page area.

## Python API

```python
from pdf_text_extractor import extract_pdf_text, inject_text_to_pdf
import os

api_key = os.environ['ANTHROPIC_API_KEY']

# Extract text
def progress(page, total):
    print(f"Processing page {page}/{total}")

extract_pdf_text('input.pdf', 'output.txt', api_key, progress)

# Inject into PDF
inject_text_to_pdf('input.pdf', 'searchable.pdf', 'output.txt')
```

## Important Implementation Notes

### API Keys
- Claude mode requires `ANTHROPIC_API_KEY` via `.env` file, environment variable, or CLI argument
- Gemini mode requires `GOOGLE_API_KEY` via `.env` file, environment variable, or CLI argument
- Both CLI tools (`pdf-extract` and `pdf-batch`) automatically load `.env` file from current directory
- API key priority: CLI argument > environment variable > `.env` file
- Local/spaCy mode requires no API key but needs `pip install ".[local]"` + spaCy model
- **Recommended approach**: Create a `.env` file from `.env.example` and add your API keys there

### Model Versions
- **Claude**: Uses `claude-sonnet-4-5-20250929` hardcoded in [extractor.py:179](pdf_text_extractor/extractor.py#L179)
- **Gemini**: Uses `gemini-2.5-flash-image` with the new `google-genai` SDK (v1.57.0+) - provides higher quota limits than the 2.0 experimental model
- Update these model IDs when new versions are released

### Image Resolution
PDF pages are rendered at 2x resolution (Matrix(2, 2)) in `pdf_to_images()` for better OCR quality. Higher resolution = better accuracy but larger image size and higher API costs.

### Error Handling
The batch processor will stop and report errors when API issues are detected mid-extraction. This prevents incomplete/corrupted output files. Check the error patterns in `contains_api_error()` if adding new error detection.

### Output Format Behavior
- `--format=markdown`: Creates `.md` files, preserves document structure (headings, lists, tables)
- `--format=plain`: Creates `.txt` files, simple text extraction
- `--save-plain`: When using markdown, also generates `.txt` for PDF injection (best of both worlds)
- PDF injection always uses plain text (markdown formatting would appear as literal text in PDF)

### Batch Processing Skip Logic
The batch processor skips files if:
1. Output file exists AND
2. Output file contains no API errors AND
3. `--no-skip` flag not set

Files with API errors are automatically reprocessed even if they exist.

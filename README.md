# PDF Text Extractor

Vision-based text extraction from scanned PDFs using Claude AI's multimodal capabilities.

## Why This Tool?

Traditional OCR tools like Tesseract can struggle with:
- Complex layouts (multi-column documents)
- Poor scan quality
- Mixed fonts and formatting
- Tables and special formatting

This tool uses Claude's vision capabilities to "read" PDFs like a human would, producing clean, well-formatted text even from challenging scans.

## Features

- **Vision-based extraction**: Uses Claude AI to visually read and extract text
- **Clean output**: Preserves formatting and layout better than traditional OCR
- **PDF injection**: Create searchable PDFs by injecting extracted text as invisible layers
- **Simple CLI**: Easy-to-use command-line tools

## Installation

### Basic Installation (Claude mode only)

```bash
pip install .
```

### Installation with Local Mode Support

```bash
# Install with local mode dependencies
pip install ".[local]"

# Download the spaCy language model
python -m spacy download en_core_web_sm
```

### Development Installation

```bash
pip install -e ".[local]"
python -m spacy download en_core_web_sm
```

## Requirements

- Python 3.10+ (required for spacy-layout)
- Anthropic API key for Claude mode (get one at https://console.anthropic.com/)
- For local mode: spacy-layout library (see installation below)

## Development / Virtual Environment

For development it's recommended to create an isolated virtual environment in the project directory and install the package in editable mode.

```bash
# Create a venv named .venv
python3 -m venv .venv

# Activate (bash/zsh)
source .venv/bin/activate

# Upgrade packaging tools and install in editable mode
python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

If you're using `zsh` on macOS (default), the `source .venv/bin/activate` command will put you into the virtual environment; run `deactivate` to exit.

## Usage

### 1. Batch Process (Recommended)

Process entire directory trees with one command:

```bash
# Set your API key
export ANTHROPIC_API_KEY='your-key-here'

# Process all PDFs, creating *_searchable.pdf files
pdf-batch /path/to/pdfs

# Overwrite original PDFs with searchable versions
pdf-batch --overwrite /path/to/pdfs

# Reprocess everything (ignore existing .txt files)
pdf-batch --no-skip /path/to/pdfs
```

This will:
- Recursively find all PDFs in the directory
- Extract text and save as `.txt` next to each PDF
- Create searchable PDFs (either new `*_searchable.pdf` or overwrite originals)
- Skip already-processed files by default
- Show progress for each file

### 2. Extract Text from PDF

```bash
# Set your API key
export ANTHROPIC_API_KEY='your-key-here'

# Extract text
pdf-extract input.pdf output.txt
```

Or pass the API key directly:

```bash
pdf-extract input.pdf output.txt sk-ant-...
```

The output file will contain page-separated text:

```
=== PAGE 1 ===
[text from page 1]

=== PAGE 2 ===
[text from page 2]
```

### 3. Inject Text into PDF

Create a searchable PDF by injecting the extracted text as an invisible layer:

```bash
pdf-inject input.pdf searchable.pdf output.txt
```

The resulting PDF will:
- Look identical to the original
- Be fully searchable (Cmd+F / Ctrl+F)
- Allow text selection and copying
- Work with `pdftotext` and other tools

## Example Workflows

### Batch Process an Archive

```bash
# Set your API key once
export ANTHROPIC_API_KEY='your-key-here'

# Process entire directory tree
pdf-batch ~/Documents/scanned-archive

# Result: All PDFs get .txt files and *_searchable.pdf versions
# Existing files are skipped automatically
```

### Single File

```bash
# 1. Extract text from scanned PDF
export ANTHROPIC_API_KEY='your-key-here'
pdf-extract scanned_document.pdf extracted_text.txt

# 2. Create searchable PDF
pdf-inject scanned_document.pdf searchable_document.pdf extracted_text.txt

# 3. Verify it works
pdftotext searchable_document.pdf - | head -20
```

## Python API

You can also use the tools programmatically:

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

## Cost Considerations

This tool uses Claude Sonnet 4.5 for vision-based extraction. Pricing:
- ~$0.003 per page (at current API rates)
- For a 100-page document: ~$0.30

This is competitive with commercial OCR services and often produces better results for complex documents.

## Comparison with Traditional OCR

| Feature | pdf-text-extractor | Tesseract OCR |
|---------|-------------------|---------------|
| Complex layouts | ✓ Excellent | ✗ Often jumbled |
| Poor quality scans | ✓ Good | ~ Variable |
| Tables | ✓ Good | ✗ Poor |
| Multi-column | ✓ Excellent | ✗ Often fails |
| Setup | Simple | Complex |
| Speed | Moderate | Fast |
| Cost | API costs | Free |

## License

MIT

## Credits

Built with:
- [Anthropic Claude AI](https://www.anthropic.com/) for vision-based text extraction
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF manipulation

## Local Mode (No API Key Required)

For offline processing without using the Claude API, you can use the local/spacy mode which leverages the spacy-layout library for layout-aware text extraction with OCR support:

```bash
# Extract text using local mode (no API key needed)
pdf-extract input.pdf output.txt --mode=spacy

# Batch process using local mode
pdf-batch --mode=spacy /path/to/pdfs
```

### Install spaCy Layout for Local Mode

The local mode requires spacy-layout and the spaCy language model:

```shell
# Activate venv then install dependencies
source .venv/bin/activate
pip install spacy-layout
python -m spacy download en_core_web_sm
```

**Features of Local Mode:**
- Uses spacy-layout library for document structure understanding
- Supports both PDFs with embedded text and scanned documents
- Integrated OCR capabilities via the Docling library
- No API costs - completely offline processing
- Layout-aware text extraction preserves document structure

**When to Use Each Mode:**
- **Claude Mode**: Best for complex layouts, poor quality scans, and highest accuracy
- **Local Mode**: Good for offline processing, cost-free operation, and standard document quality
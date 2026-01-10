# PDF Text Extractor

Vision-based text extraction from scanned PDFs using AI vision models (Claude or Gemini).

## Why This Tool?

Traditional OCR tools like Tesseract can struggle with:
- Complex layouts (multi-column documents)
- Poor scan quality
- Mixed fonts and formatting
- Tables and special formatting

This tool uses AI vision capabilities to "read" PDFs like a human would, producing clean, well-formatted text even from challenging scans.

## Features

- **Multiple AI providers**: Choose between Claude (Anthropic) or Gemini (Google) for vision-based extraction
- **Markdown output**: Preserves document structure with headings, lists, and formatting
- **Dual-output mode**: Generate both markdown (for reading) and plain text (for PDF injection)
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
- API key for AI modes:
  - **Claude**: Get an Anthropic API key at https://console.anthropic.com/
  - **Gemini**: Get a Google API key at https://aistudio.google.com/apikey
  - API keys can be set via environment variables or in a `.env` file
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

## API Key Configuration

API keys can be configured in three ways (in order of precedence):

1. **Command-line argument**: Pass the API key directly to the command
2. **Environment variable**: Set `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY`
3. **.env file**: Create a `.env` file in your current directory (recommended)

### Using a .env file (Recommended)

Create a `.env` file in your current directory:

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=AIza-your-key-here
```

The tools will automatically load API keys from this file. **Note:** Make sure to add `.env` to your `.gitignore` to avoid committing your API keys!

### Using Environment Variables

```bash
# For Claude
export ANTHROPIC_API_KEY='your-key-here'

# For Gemini
export GOOGLE_API_KEY='your-key-here'
```

## Usage

### 1. Batch Process (Recommended)

Process entire directory trees with one command:

```bash
# Process all PDFs with markdown output (default)
# Creates .md files and *_searchable.pdf files
# API key will be loaded from .env file
pdf-batch /path/to/pdfs

# Also save plain .txt files for PDF injection
pdf-batch --save-plain /path/to/pdfs

# Use plain text format only
pdf-batch --format=plain /path/to/pdfs

# Overwrite original PDFs with searchable versions
pdf-batch --overwrite /path/to/pdfs

# Reprocess everything (ignore existing files)
pdf-batch --no-skip /path/to/pdfs
```

**New format options:**
- `--format=markdown` (default): Creates `.md` files with preserved structure
- `--format=plain`: Creates `.txt` files with plain text
- `--save-plain`: When using markdown, also saves `.txt` files for PDF injection

This will:
- Recursively find all PDFs in the directory
- Extract text in chosen format (default: markdown)
- Create searchable PDFs (either new `*_searchable.pdf` or overwrite originals)
- Skip already-processed files by default
- Show progress for each file

### 2. Extract Text from PDF

```bash
# Using Claude (default)
# API key will be loaded from .env file
pdf-extract input.pdf output.md

# Using Google Gemini
# API key will be loaded from .env file
pdf-extract input.pdf output.md --mode=gemini

# Or set environment variables directly
export ANTHROPIC_API_KEY='your-key-here'
pdf-extract input.pdf output.md

# Extract as plain text (for PDF injection)
pdf-extract input.pdf output.txt --format=plain

# Generate both markdown AND plain text versions
pdf-extract input.pdf output.md --plain-output=output.txt
```

Or pass the API key directly:

```bash
# Claude
pdf-extract input.pdf output.md sk-ant-...

# Gemini
pdf-extract input.pdf output.md --mode=gemini AIza...
```

#### Markdown Output (Default)

The default markdown format preserves document structure:

```markdown
=== PAGE 1 ===
# Document Title

## Section 1.1

This is a paragraph with **bold text**.

- Bullet point 1
- Bullet point 2

## Section 1.2

More content here.

=== PAGE 2 ===
# Another Section
...
```

#### Plain Text Output

Use `--format=plain` for simple text extraction without markdown formatting:

```
=== PAGE 1 ===
Document Title

Section 1.1

This is a paragraph with bold text.

Bullet point 1
Bullet point 2
...
```

#### Dual-Output Mode

For the best of both worlds, use `--plain-output` to generate both versions in one pass:

```bash
# Creates output.md (markdown) and output_plain.txt (plain text)
pdf-extract scan.pdf output.md --plain-output=output_plain.txt

# Then use the plain text version for PDF injection
pdf-inject scan.pdf searchable.pdf output_plain.txt
```

This is ideal when you want readable markdown for documentation AND clean text for PDF searchability.

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

### Batch Process an Archive (Markdown Mode)

```bash
# Create .env file with your API key (one-time setup)
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# Process entire directory tree with markdown output
pdf-batch ~/Documents/scanned-archive

# Result: All PDFs get .md files and *_searchable.pdf versions
# The .md files preserve document structure with headings, lists, etc.
# Existing files are skipped automatically
```

### Batch Process with Dual-Output

```bash
# Generate both markdown AND plain text files
pdf-batch --save-plain ~/Documents/scanned-archive

# Result:
# - .md files for readable, structured documentation
# - .txt files for searchable PDF injection
# - *_searchable.pdf files with clean text layers
```

### Single File with Markdown

```bash
# 1. Extract text as markdown with plain text version
# (API key loaded from .env file)
pdf-extract scanned_document.pdf document.md --plain-output=document.txt

# 2. Create searchable PDF using the plain text version
pdf-inject scanned_document.pdf searchable_document.pdf document.txt

# 3. Verify it works
pdftotext searchable_document.pdf - | head -20

# 4. Read the markdown version for structured content
cat document.md
```

### Single File (Plain Text Only)

```bash
# 1. Extract text as plain text
# (API key loaded from .env file)
pdf-extract scanned_document.pdf extracted_text.txt --format=plain

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

### Claude (Anthropic)
Uses Claude Sonnet 4.5 for vision-based extraction:
- Input: $3 per million tokens (~2,000 tokens per page for 2x resolution images)
- Output: $15 per million tokens (~750 tokens per page for extracted text)
- **~$0.018 per page** (at current API rates)
- For a 100-page document: ~$1.80
- Excellent quality for complex layouts
- See [Anthropic pricing](https://www.anthropic.com/pricing) for latest rates

### Gemini (Google)
Uses Gemini 2.0 Flash (experimental) for vision-based extraction:
- ~$0.0001 per page (free tier available, then very low cost)
- For a 100-page document: ~$0.01
- Good quality, significantly lower cost

Both options are competitive with commercial OCR services and often produce better results for complex documents.

## Choosing Between Claude and Gemini

| Aspect | Claude Sonnet 4.5 | Gemini 2.0 Flash |
|--------|-------------------|------------------|
| **Cost** | ~$0.018/page | ~$0.0001/page (180x cheaper) |
| **Quality** | Excellent | Good |
| **Best For** | Critical documents, complex layouts | Bulk processing, cost-sensitive |
| **Speed** | Fast | Very fast |
| **Free Tier** | $5 credit for new accounts | Generous free quota |

**Recommendation:**
- Use **Claude** for important documents where accuracy is critical
- Use **Gemini** for bulk processing or when cost is a concern
- Try both on a sample to see which works better for your specific documents

**Note:** Costs can vary based on document complexity, image resolution, and output length. The CLI tools now display timing information to help you track processing speed.

## Comparison with Traditional OCR

| Feature | pdf-text-extractor (Claude) | pdf-text-extractor (Gemini) | Tesseract OCR |
|---------|-------------------|------------------|---------------|
| Complex layouts | ✓ Excellent | ✓ Good | ✗ Often jumbled |
| Poor quality scans | ✓ Good | ✓ Good | ~ Variable |
| Tables | ✓ Good | ✓ Good | ✗ Poor |
| Multi-column | ✓ Excellent | ✓ Good | ✗ Often fails |
| Setup | Simple | Simple | Complex |
| Speed | Fast (~5-10s/page) | Very fast | Very fast |
| Cost | ~$0.018/page | ~$0.0001/page | Free |

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
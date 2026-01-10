# Batch Processing Guide

## Quick Start

```bash
# Set your API key (do this once)
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Process all PDFs in a directory
pdf-batch /path/to/pdfs
```

## What It Does

The `pdf-batch` command will:

1. **Find** all PDF files recursively in the directory
2. **Extract** text from each PDF using Claude's vision
3. **Save** extracted text as `.txt` next to each PDF
4. **Create** searchable PDFs (either `*_searchable.pdf` or overwrite originals)
5. **Skip** already-processed files (smart resume)
6. **Show** progress for each file

## Modes

### Default Mode (Safe)

Creates new files, keeps originals:

```bash
pdf-batch /path/to/archive
```

Result:
```
archive/
  document.pdf              ← Original (unchanged)
  document.txt              ← Extracted text
  document_searchable.pdf   ← New searchable version
```

### Overwrite Mode (Replace Originals)

Replaces original PDFs with searchable versions:

```bash
pdf-batch --overwrite /path/to/archive
```

⚠️ **Warning:** This will ask for confirmation before proceeding!

Result:
```
archive/
  document.pdf   ← Now searchable!
  document.txt   ← Extracted text
```

### Reprocess Mode

Process everything, even if `.txt` files already exist:

```bash
pdf-batch --no-skip /path/to/archive
```

## Example Workflows

### Process Your Entire Archive

```bash
# Navigate to your archive
cd "/Users/csvensson/Library/CloudStorage/GoogleDrive-ephemeris.production@sjaa.net/My Drive/1954-2004 Back Issues"

# Process everything (creates *_searchable.pdf files)
pdf-batch .

# This will process:
# - Seventies/7001/Eph70_01.pdf
# - Seventies/7002/Eph70_02.pdf
# - ... hundreds more ...
# - Naughts/0411/EphNov04.pdf
```

### Process Just One Decade

```bash
# Process only 1970s documents
pdf-batch Seventies

# Process only 2000s documents
pdf-batch Naughts
```

### Resume After Interruption

If you stop the process (Ctrl+C), you can resume:

```bash
# Just run the same command again
pdf-batch Seventies

# It will skip files that already have .txt files
```

### Reprocess with Better Results

If Claude improves or you want to re-extract:

```bash
# Force reprocessing of everything
pdf-batch --no-skip Seventies
```

## Progress Tracking

The tool shows detailed progress:

```
Found 150 PDF files
Mode: Create new files (*_searchable.pdf)
Skip existing: Yes

[1/150] Seventies/7001/Eph70_01.pdf
  → Extracting text...
    Page 5/5
  ✓ Text extracted: Eph70_01.txt
  → Creating searchable PDF...
  ✓ Created: Eph70_01_searchable.pdf

[2/150] Seventies/7002/Eph70_02.pdf
  ⊙ Skipping (text file exists)

[3/150] Seventies/7003/Eph70_03.pdf
  → Extracting text...
...
```

## Interrupting Safely

- Press `Ctrl+C` to stop at any time
- Current file processing will stop
- Already-processed files are safe
- Incomplete files are cleaned up
- Just re-run to resume

## Cost Estimation

Before batch processing, estimate the cost:

```bash
# Count total pages in your archive
find Seventies -name "*.pdf" -exec pdfinfo {} \; | grep Pages | awk '{sum+=$2} END {print sum " pages"}'

# Multiply by $0.003 per page
```

Example:
- 500 pages × $0.003 = $1.50
- 2000 pages × $0.003 = $6.00

## File Organization

### Before
```
archive/
  ├── folder1/
  │   ├── doc1.pdf
  │   └── doc2.pdf
  └── folder2/
      └── doc3.pdf
```

### After (Default Mode)
```
archive/
  ├── folder1/
  │   ├── doc1.pdf
  │   ├── doc1.txt ← NEW
  │   ├── doc1_searchable.pdf ← NEW
  │   ├── doc2.pdf
  │   ├── doc2.txt ← NEW
  │   └── doc2_searchable.pdf ← NEW
  └── folder2/
      ├── doc3.pdf
      ├── doc3.txt ← NEW
      └── doc3_searchable.pdf ← NEW
```

### After (Overwrite Mode)
```
archive/
  ├── folder1/
  │   ├── doc1.pdf ← Now searchable!
  │   ├── doc1.txt ← NEW
  │   ├── doc2.pdf ← Now searchable!
  │   └── doc2.txt ← NEW
  └── folder2/
      ├── doc3.pdf ← Now searchable!
      └── doc3.txt ← NEW
```

## Tips

1. **Start small**: Test on a single folder first
2. **Check quality**: Review a few extracted .txt files
3. **Keep text files**: They're useful for full-text search
4. **Use default mode**: Safer than overwrite, you can always delete originals later
5. **Monitor cost**: Check API usage at console.anthropic.com

## Troubleshooting

### "Directory not found"
```bash
# Use absolute path or check your current directory
pwd
pdf-batch "$(pwd)/Seventies"
```

### "API key not set"
```bash
# Set it in your terminal
export ANTHROPIC_API_KEY='sk-ant-...'

# Or add to your shell config
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
```

### Rate limiting
If you get rate limited, the tool will show errors. Just wait a bit and re-run (it will skip completed files).

### Low disk space
Each searchable PDF is similar in size to the original. Make sure you have enough space:
```bash
# Check available space
df -h .
```

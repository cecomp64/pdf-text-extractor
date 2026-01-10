#!/usr/bin/env python3
"""
Example: Batch process multiple PDFs.

This script shows how to process multiple PDFs in a directory,
extracting text and creating searchable versions.
"""

import os
import sys
from pathlib import Path
from pdf_text_extractor import extract_pdf_text, inject_text_to_pdf


def batch_process(input_dir, output_dir, api_key):
    """Process all PDFs in a directory."""

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all PDFs
    pdf_files = list(input_path.glob("**/*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files")
    print()

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")

        # Create output filenames
        base_name = pdf_file.stem
        text_file = output_path / f"{base_name}.txt"
        searchable_pdf = output_path / f"{base_name}_searchable.pdf"

        # Skip if already processed
        if searchable_pdf.exists():
            print(f"  ⊙ Skipping (already exists)")
            continue

        try:
            # Extract text
            print(f"  → Extracting text...")

            def progress(page, total):
                print(f"    Page {page}/{total}", end='\r')

            extract_pdf_text(str(pdf_file), str(text_file), api_key, progress)
            print(f"  ✓ Text extracted: {text_file.name}")

            # Inject into PDF
            print(f"  → Creating searchable PDF...")
            inject_text_to_pdf(str(pdf_file), str(searchable_pdf), str(text_file))
            print(f"  ✓ Searchable PDF: {searchable_pdf.name}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

        print()

    print("Batch processing complete!")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python batch_process.py <input_dir> <output_dir>")
        print()
        print("Requires ANTHROPIC_API_KEY environment variable.")
        print()
        print("Example:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("  python batch_process.py ./scans ./processed")
        sys.exit(1)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    batch_process(sys.argv[1], sys.argv[2], api_key)

"""
Command-line interface for PDF text extraction.
"""

import sys
import os
from .extractor import extract_pdf_text


def main():
    """Main CLI entry point for pdf-extract command."""

    if len(sys.argv) < 3:
        print("pdf-extract - Vision-based PDF text extraction using Claude AI")
        print()
        print("Usage: pdf-extract <input.pdf> <output.txt> [api_key]")
        print()
        print("Extracts text from scanned PDFs using Claude's vision capabilities.")
        print("Requires ANTHROPIC_API_KEY environment variable or pass as 3rd argument.")
        print()
        print("Example:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("  pdf-extract scan.pdf output.txt")
        print()
        print("The output file will contain page markers like:")
        print("  === PAGE 1 ===")
        print("  [text from page 1]")
        print("  === PAGE 2 ===")
        print("  [text from page 2]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_txt = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 else os.environ.get('ANTHROPIC_API_KEY')

    if not os.path.exists(input_pdf):
        print(f"Error: Input file not found: {input_pdf}", file=sys.stderr)
        sys.exit(1)

    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'", file=sys.stderr)
        print("Or pass as 3rd argument: pdf-extract input.pdf output.txt YOUR_API_KEY", file=sys.stderr)
        sys.exit(1)

    print(f"Converting PDF to images: {input_pdf}")

    def progress(page, total):
        print(f"  Processing page {page}/{total}...", flush=True)

    try:
        total_pages = extract_pdf_text(input_pdf, output_txt, api_key, progress)
        print(f"\n✓ Text extracted successfully: {output_txt}")
        print(f"  Total pages: {total_pages}")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

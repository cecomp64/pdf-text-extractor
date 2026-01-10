"""
Command-line interface for injecting text into PDFs.
"""

import sys
import os
from .injector import inject_text_to_pdf


def main():
    """Main CLI entry point for pdf-inject command."""

    if len(sys.argv) != 4:
        print("pdf-inject - Inject extracted text into PDFs as searchable layer")
        print()
        print("Usage: pdf-inject <input.pdf> <output.pdf> <text_file.txt>")
        print()
        print("Takes a scanned PDF and a text file (with page markers) and creates")
        print("a new PDF with an invisible searchable text layer.")
        print()
        print("The text file should have page markers like:")
        print("  === PAGE 1 ===")
        print("  [text from page 1]")
        print("  === PAGE 2 ===")
        print("  [text from page 2]")
        print()
        print("Example:")
        print("  pdf-inject scan.pdf searchable.pdf extracted.txt")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    text_file = sys.argv[3]

    if not os.path.exists(input_pdf):
        print(f"Error: Input PDF not found: {input_pdf}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(text_file):
        print(f"Error: Text file not found: {text_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Injecting text layer into: {input_pdf}")
    print(f"Using text from: {text_file}")

    try:
        total_pages = inject_text_to_pdf(input_pdf, output_pdf, text_file)
        print(f"\n✓ Searchable PDF created: {output_pdf}")
        print(f"  Total pages: {total_pages}")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

"""
Command-line interface for PDF text extraction.
"""

import sys
import os
from .extractor import extract_pdf_text_with_mode


def main():
    """Main CLI entry point for pdf-extract command."""

    if len(sys.argv) < 3:
        print("pdf-extract - Vision-based PDF text extraction using Claude AI")
        print()
        print("Usage: pdf-extract <input.pdf> <output.txt> [api_key] [--mode=claude|spacy]")
        print()
        print("Extracts text from scanned PDFs using Claude (default) or local layout/OCR.")
        print("Requires ANTHROPIC_API_KEY when using mode=claude; local mode does not require an API key.")
        print()
        print("Example:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("  pdf-extract scan.pdf output.txt")
        print("  pdf-extract scan.pdf output.txt --mode=spacy")
        print()
        print("The output file will contain page markers like:")
        print("  === PAGE 1 ===")
        print("  [text from page 1]")
        print("  === PAGE 2 ===")
        print("  [text from page 2]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_txt = sys.argv[2]
    # Parse optional args: api_key and --mode=claude|spacy
    api_key = None
    mode = 'claude'

    # Collect positional args and flags (support both `--mode=spacy` and `--mode spacy`)
    other_args = sys.argv[3:]
    i = 0
    while i < len(other_args):
        arg = other_args[i]
        if arg.startswith('--mode='):
            mode = arg.split('=', 1)[1]
        elif arg == '--mode' or arg == '-m':
            if i + 1 < len(other_args):
                mode = other_args[i + 1]
                i += 1
            else:
                print('Error: --mode requires a value', file=sys.stderr)
                sys.exit(1)
        else:
            # treat as api_key if present
            api_key = arg
        i += 1

    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')

    if not os.path.exists(input_pdf):
        print(f"Error: Input file not found: {input_pdf}", file=sys.stderr)
        sys.exit(1)

    # Only require API key when using Claude mode
    if mode == 'claude' and not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set (required for mode=claude)", file=sys.stderr)
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'", file=sys.stderr)
        print("Or pass as 3rd argument: pdf-extract input.pdf output.txt YOUR_API_KEY", file=sys.stderr)
        sys.exit(1)

    print(f"Converting PDF to images: {input_pdf} (mode={mode})")

    def progress(page, total):
        print(f"  Processing page {page}/{total}...", flush=True)

    try:
        total_pages = extract_pdf_text_with_mode(input_pdf, output_txt, api_key=api_key, progress_callback=progress, mode=mode)
        print(f"\n✓ Text extracted successfully: {output_txt}")
        print(f"  Total pages: {total_pages}")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

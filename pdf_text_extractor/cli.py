"""
Command-line interface for PDF text extraction.
"""

import sys
import os
from dotenv import load_dotenv
from .extractor import extract_pdf_text_with_mode

# Load environment variables from .env file
load_dotenv()


def main():
    """Main CLI entry point for pdf-extract command."""

    if len(sys.argv) < 3:
        print("pdf-extract - Vision-based PDF text extraction using AI")
        print()
        print("Usage: pdf-extract <input.pdf> <output.md> [api_key] [options]")
        print()
        print("Options:")
        print("  --mode=claude|gemini|spacy   Extraction mode (default: claude)")
        print("  --format=markdown|plain      Output format (default: markdown)")
        print()
        print("Extracts text from scanned PDFs using AI vision or local layout/OCR.")
        print("Requires ANTHROPIC_API_KEY for Claude or GOOGLE_API_KEY for Gemini.")
        print("API keys can be set via environment variables or in a .env file.")
        print("Local mode (spacy) does not require an API key.")
        print()
        print("Examples:")
        print("  # Using Claude (default) - generates markdown for readability")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("  pdf-extract scan.pdf output.md")
        print()
        print("  # Using Google Gemini")
        print("  export GOOGLE_API_KEY='your-key-here'")
        print("  pdf-extract scan.pdf output.md --mode=gemini")
        print()
        print("  # Other options")
        print("  pdf-extract scan.pdf output.txt --format=plain")
        print("  pdf-extract scan.pdf output.txt --mode=spacy")
        print()
        print("Note: To create searchable PDFs, use pdf-inject with spaCy OCR:")
        print("  pdf-inject scan.pdf searchable.pdf")
        print()
        print("The output file will contain page markers like:")
        print("  === PAGE 1 ===")
        print("  [text from page 1]")
        print("  === PAGE 2 ===")
        print("  [text from page 2]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_txt = sys.argv[2]
    # Parse optional args: api_key, --mode, --format
    api_key = None
    mode = 'claude'
    output_format = 'markdown'

    # Collect positional args and flags
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
        elif arg.startswith('--format='):
            output_format = arg.split('=', 1)[1]
        elif arg == '--format' or arg == '-f':
            if i + 1 < len(other_args):
                output_format = other_args[i + 1]
                i += 1
            else:
                print('Error: --format requires a value', file=sys.stderr)
                sys.exit(1)
        else:
            # treat as api_key if present
            api_key = arg
        i += 1

    # Get API key based on mode
    if mode == 'gemini':
        api_key = api_key or os.environ.get('GOOGLE_API_KEY')
    else:
        api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')

    if not os.path.exists(input_pdf):
        print(f"Error: Input file not found: {input_pdf}", file=sys.stderr)
        sys.exit(1)

    # Require API key when using AI modes
    if mode == 'claude' and not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set (required for mode=claude)", file=sys.stderr)
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'", file=sys.stderr)
        print("Or pass as 3rd argument: pdf-extract input.pdf output.txt YOUR_API_KEY", file=sys.stderr)
        sys.exit(1)
    elif mode == 'gemini' and not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set (required for mode=gemini)", file=sys.stderr)
        print("Set it with: export GOOGLE_API_KEY='your-key-here'", file=sys.stderr)
        print("Or pass as 3rd argument: pdf-extract input.pdf output.txt YOUR_API_KEY", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting text: {input_pdf} (mode={mode}, format={output_format})")

    def progress(page, total):
        print(f"  Processing page {page}/{total}...", flush=True)

    try:
        total_pages, page_timings, total_time = extract_pdf_text_with_mode(
            input_pdf,
            output_txt,
            api_key=api_key,
            progress_callback=progress,
            mode=mode,
            output_format=output_format
        )
        print(f"\n✓ Text extracted successfully: {output_txt}")
        print(f"  Total pages: {total_pages}")
        print(f"  Total time: {total_time:.1f}s")
        if page_timings:
            avg_time = sum(t for _, t in page_timings) / len(page_timings)
            print(f"  Average per page: {avg_time:.1f}s")
            # Show slowest and fastest pages
            if len(page_timings) > 1:
                slowest = max(page_timings, key=lambda x: x[1])
                fastest = min(page_timings, key=lambda x: x[1])
                print(f"  Fastest page: {fastest[0]} ({fastest[1]:.1f}s)")
                print(f"  Slowest page: {slowest[0]} ({slowest[1]:.1f}s)")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

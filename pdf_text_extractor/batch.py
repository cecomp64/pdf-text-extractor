"""
Command-line interface for batch processing PDFs.
"""

import sys
import os
from pathlib import Path
import fitz  # PyMuPDF
from dotenv import load_dotenv
from .extractor import extract_pdf_text_with_mode, contains_api_error
from .injector import inject_text_to_pdf

# Load environment variables from .env file
load_dotenv()


def find_pdfs(directory):
    """Recursively find all PDF files in directory."""
    path = Path(directory)
    return sorted(path.rglob("*.pdf"))


def estimate_cost(pdf_files, skip_existing=True, mode='claude'):
    """
    Estimate the cost of processing PDFs.

    Args:
        pdf_files: List of PDF file paths
        skip_existing: Whether to skip files that already have output
        mode: Extraction mode ('claude', 'gemini', 'spacy', or 'local')

    Returns:
        (total_pdfs, pdfs_to_process, pdfs_with_errors, total_pages, estimated_cost)
    """
    total_pdfs = len(pdf_files)
    pdfs_to_process = []
    pdfs_with_errors = []
    total_pages = 0

    print("Analyzing PDFs for cost estimation...")

    for pdf_file in pdf_files:
        # Check if already processed
        txt_file = pdf_file.with_suffix('.txt')
        should_process = False

        if skip_existing and txt_file.exists():
            # Check if the text file contains API errors
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if contains_api_error(content):
                    # File has errors, need to reprocess
                    should_process = True
                    pdfs_with_errors.append(pdf_file)
                else:
                    # File is good, skip it
                    continue
            except Exception:
                # Can't read file, better to reprocess
                should_process = True
                pdfs_with_errors.append(pdf_file)
        else:
            # File doesn't exist or skip_existing is False
            should_process = True

        if should_process:
            pdfs_to_process.append(pdf_file)

            # Count pages
            try:
                doc = fitz.open(str(pdf_file))
                page_count = len(doc)
                doc.close()
                total_pages += page_count
            except Exception:
                # Assume average of 5 pages if we can't open it
                total_pages += 5

    # Cost calculation based on mode:
    #
    # Claude Sonnet 4.5:
    #   Input: $3 per million tokens, ~2,000 tokens per page (2x resolution image)
    #   Output: $15 per million tokens, ~750 tokens per page (extracted text)
    #   Input cost: 2,000 × $3/1M = $0.006
    #   Output cost: 750 × $15/1M = $0.01125
    #   Total: ~$0.018 per page
    #
    # Gemini 2.0 Flash:
    #   Input: $0.075 per million tokens, ~2,000 tokens per page
    #   Output: $0.30 per million tokens, ~750 tokens per page
    #   Input cost: 2,000 × $0.075/1M = $0.00015
    #   Output cost: 750 × $0.30/1M = $0.000225
    #   Total: ~$0.0001 per page (rounded to 4 decimal places)
    #
    # spaCy/local: Free (no API cost)

    if mode == 'gemini':
        cost_per_page = 0.0001
    elif mode in ['spacy', 'local']:
        cost_per_page = 0.0
    else:  # claude (default)
        cost_per_page = 0.018

    estimated_cost = total_pages * cost_per_page

    return total_pdfs, len(pdfs_to_process), pdfs_with_errors, total_pages, estimated_cost


def batch_process(directory, api_key, overwrite=False, skip_existing=True, auto_confirm=False, mode='claude', output_format='markdown', ocr_only=False, skip_ocr=False):
    """
    Batch process all PDFs in a directory tree.

    Args:
        directory: Root directory to search
        api_key: Anthropic API key (not needed if ocr_only=True)
        overwrite: If True, overwrite original PDFs. If False, create *_searchable.pdf
        skip_existing: If True, skip PDFs that already have text files
        auto_confirm: If True, skip confirmation prompt
        mode: Extraction mode ('claude', 'gemini', or 'spacy')
        output_format: Output format ('markdown' or 'plain')
        ocr_only: If True, only create searchable PDFs using OCR (skip text extraction)
        skip_ocr: If True, only do text extraction (skip creating searchable PDFs)
    """

    pdf_files = find_pdfs(directory)

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return

    # Estimate cost (only if not OCR-only mode)
    if not ocr_only:
        total_pdfs, pdfs_to_process, pdfs_with_errors, total_pages, estimated_cost = estimate_cost(pdf_files, skip_existing, mode)
    else:
        # In OCR-only mode, process all PDFs or skip based on searchable PDF existence
        total_pdfs = len(pdf_files)
        pdfs_to_process = 0
        pdfs_with_errors = []
        total_pages = 0
        estimated_cost = 0.0

        for pdf_file in pdf_files:
            output_pdf = pdf_file.with_stem(f"{pdf_file.stem}_searchable") if not overwrite else pdf_file

            if skip_existing and output_pdf.exists() and output_pdf != pdf_file:
                continue

            pdfs_to_process += 1
            # Count pages for progress tracking
            try:
                doc = fitz.open(str(pdf_file))
                total_pages += len(doc)
                doc.close()
            except Exception:
                total_pages += 5  # Assume 5 pages if can't open

    # Show summary
    print()
    print("=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total PDFs found:        {total_pdfs}")
    print(f"Already processed:       {total_pdfs - pdfs_to_process}")
    if pdfs_with_errors:
        print(f"With API errors:         {len(pdfs_with_errors)} (will be reprocessed)")
    print(f"To be processed:         {pdfs_to_process}")
    print(f"Total pages:             {total_pages}")
    if not ocr_only:
        print(f"Estimated cost:          ${estimated_cost:.2f}")
    print()
    if not skip_ocr:
        print(f"Mode: {'OVERWRITE originals' if overwrite else 'Create new files (*_searchable.pdf)'}")
    print(f"Skip existing: {'Yes' if skip_existing else 'No'}")
    if ocr_only:
        print(f"Operation: OCR only (no text extraction)")
    elif skip_ocr:
        print(f"Operation: Text extraction only (no searchable PDFs)")
        print(f"Extraction mode: {mode}")
        print(f"Output format: {output_format}")
    else:
        print(f"Extraction mode: {mode}")
        print(f"Output format: {output_format}")
    print("=" * 60)

    # Show files with errors if any
    if pdfs_with_errors:
        print()
        print(f"Files with API errors detected ({len(pdfs_with_errors)}):")
        for pdf_file in pdfs_with_errors:
            print(f"  ⚠ {pdf_file.relative_to(directory)}")
        print("=" * 60)

    print()

    if pdfs_to_process == 0:
        print("✓ All PDFs already processed! Use --no-skip to reprocess.")
        return

    # Prompt user to continue (unless auto-confirm)
    if not auto_confirm:
        try:
            if ocr_only:
                response = input(f"Process {pdfs_to_process} PDFs with OCR? [y/N]: ")
            else:
                response = input(f"Process {pdfs_to_process} PDFs (~${estimated_cost:.2f})? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Cancelled.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return
        print()
    else:
        if ocr_only:
            print(f"Auto-confirming: Processing {pdfs_to_process} PDFs with OCR")
        else:
            print(f"Auto-confirming: Processing {pdfs_to_process} PDFs (~${estimated_cost:.2f})")
        print()

    processed = 0
    skipped = 0
    errors = 0
    total_pages_processed = 0
    total_processing_time = 0.0
    file_timings = []  # Track (filename, pages, time) for each file

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_file.relative_to(directory)}")

        # Determine output paths based on format
        if output_format == 'markdown':
            main_output_file = pdf_file.with_suffix('.md')
        else:
            main_output_file = pdf_file.with_suffix('.txt')

        if overwrite:
            # Create temp file, then replace original
            output_pdf = pdf_file.with_suffix('.pdf.tmp')
            final_pdf = pdf_file
        else:
            # Create new file with _searchable suffix
            output_pdf = pdf_file.with_stem(f"{pdf_file.stem}_searchable")
            final_pdf = output_pdf

        # Check if already processed
        if not ocr_only:
            # In normal mode, check if text extraction file exists
            if skip_existing and main_output_file.exists():
                # Check if the file contains API errors
                try:
                    with open(main_output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if contains_api_error(content):
                        # File has errors, reprocess it
                        print(f"  ⚠ Reprocessing (API error detected in existing file)")
                    else:
                        # File is good, skip it
                        print(f"  ⊙ Skipping (output file exists)")
                        skipped += 1
                        continue
                except Exception:
                    # Can't read file, better to reprocess
                    print(f"  ⚠ Reprocessing (cannot read existing file)")

        # Check if searchable PDF already exists
        if skip_existing and final_pdf.exists() and final_pdf != pdf_file:
            print(f"  ⊙ Skipping (searchable PDF exists)")
            skipped += 1
            continue

        try:
            # Extract text (unless OCR-only mode)
            if not ocr_only:
                print(f"  → Extracting text...")

                def progress(page, total):
                    print(f"    Page {page}/{total}", end='\r', flush=True)

                num_pages, page_timings, file_time = extract_pdf_text_with_mode(
                    str(pdf_file),
                    str(main_output_file),
                    api_key=api_key,
                    progress_callback=progress,
                    mode=mode,
                    output_format=output_format
                )
                total_pages_processed += num_pages
                total_processing_time += file_time
                file_timings.append((pdf_file.name, num_pages, file_time))

                print(f"  ✓ Text extracted: {main_output_file.name} ({file_time:.1f}s, {num_pages} pages)          ")

            # Create searchable PDF using OCR (unless skip_ocr is set)
            if not skip_ocr:
                print(f"  → Creating searchable PDF with OCR...")
                inject_text_to_pdf(str(pdf_file), str(output_pdf))

                # If overwriting, replace original
                if overwrite:
                    os.replace(str(output_pdf), str(final_pdf))
                    print(f"  ✓ Updated: {final_pdf.name}")
                else:
                    print(f"  ✓ Created: {final_pdf.name}")

            processed += 1

        except KeyboardInterrupt:
            print(f"\n\n⚠ Interrupted by user")
            # Clean up temp file if it exists
            if output_pdf.exists() and output_pdf != final_pdf:
                output_pdf.unlink()
            break

        except Exception as e:
            print(f"  ✗ Error: {e}")
            errors += 1
            # Clean up temp file if it exists
            if output_pdf.exists() and output_pdf != final_pdf:
                output_pdf.unlink()
            continue

        print()

    # Summary
    print("=" * 60)
    print(f"Batch processing complete!")
    print(f"  Processed: {processed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {errors}")
    print(f"  Total:     {len(pdf_files)}")
    if total_pages_processed > 0:
        print(f"\n  Total pages processed: {total_pages_processed}")
        print(f"  Total processing time: {total_processing_time:.1f}s ({total_processing_time / 60:.1f} min)")
        avg_per_page = total_processing_time / total_pages_processed
        print(f"  Average time per page: {avg_per_page:.1f}s")
        if file_timings:
            # Show slowest file
            slowest_file = max(file_timings, key=lambda x: x[2] / x[1] if x[1] > 0 else 0)
            fastest_file = min(file_timings, key=lambda x: x[2] / x[1] if x[1] > 0 else float('inf'))
            if slowest_file[1] > 0:
                print(f"  Slowest file: {slowest_file[0]} ({slowest_file[2] / slowest_file[1]:.1f}s/page)")
            if fastest_file[1] > 0:
                print(f"  Fastest file: {fastest_file[0]} ({fastest_file[2] / fastest_file[1]:.1f}s/page)")


def main():
    """Main CLI entry point for pdf-batch command."""

    import argparse

    parser = argparse.ArgumentParser(
        description='Batch process PDFs with vision-based text extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process all PDFs with markdown output using Claude (default)
  # Creates .md files for readability + searchable PDFs with OCR
  pdf-batch /path/to/pdfs

  # Use Google Gemini instead of Claude
  export GOOGLE_API_KEY='your-key-here'
  pdf-batch --mode=gemini /path/to/pdfs

  # Use plain text format (faster AI extraction, no markdown)
  pdf-batch --format=plain /path/to/pdfs

  # Overwrite original PDFs with searchable versions
  pdf-batch --overwrite /path/to/pdfs

  # Reprocess everything, even if files exist
  pdf-batch --no-skip /path/to/pdfs

  # Skip confirmation prompt (auto-confirm)
  pdf-batch --yes /path/to/pdfs

  # Use local mode (no API key needed, spaCy only)
  pdf-batch --mode=spacy /path/to/pdfs

  # OCR-only mode: only create searchable PDFs (skip text extraction)
  # Useful when you already have .md files and just need searchable PDFs
  pdf-batch --ocr-only /path/to/pdfs

  # Skip OCR mode: only extract text (no searchable PDFs)
  # Useful when you only want .md files for reading
  pdf-batch --skip-ocr /path/to/pdfs

Environment Variables:
  ANTHROPIC_API_KEY    Required for mode=claude. Your Anthropic API key.
  GOOGLE_API_KEY       Required for mode=gemini. Your Google API key.

API keys can also be loaded from a .env file in the current directory.

Note: Searchable PDFs are created using spaCy Layout OCR for accurate text
positioning. The markdown/text files are separate outputs for readability.
        '''
    )

    parser.add_argument(
        'directory',
        help='Directory containing PDFs (will search recursively)'
    )

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite original PDFs instead of creating *_searchable.pdf files'
    )

    parser.add_argument(
        '--no-skip',
        action='store_true',
        help='Process all PDFs, even if text files already exist'
    )

    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )

    parser.add_argument(
        '--mode',
        choices=['claude', 'gemini', 'spacy', 'local'],
        default='claude',
        help='Extraction mode: "claude" (default) uses Anthropic, "gemini" uses Google, "spacy" uses local layout/OCR'
    )

    parser.add_argument(
        '--format',
        choices=['markdown', 'plain'],
        default='markdown',
        help='Output format: "markdown" (default) preserves structure; "plain" for simple text'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt (auto-confirm)'
    )

    parser.add_argument(
        '--ocr-only',
        action='store_true',
        help='Only create searchable PDFs using OCR (skip text extraction). No API key required.'
    )

    parser.add_argument(
        '--skip-ocr',
        action='store_true',
        help='Only extract text (skip creating searchable PDFs). Useful for generating .md files only.'
    )

    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.ocr_only and args.skip_ocr:
        print("Error: --ocr-only and --skip-ocr are mutually exclusive", file=sys.stderr)
        sys.exit(1)

    # Get API key based on mode (not needed in OCR-only mode)
    if not args.ocr_only:
        if args.mode == 'gemini':
            api_key = args.api_key or os.environ.get('GOOGLE_API_KEY')
        else:
            api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')

        # Require API key for AI modes
        if args.mode == 'claude' and not api_key:
            print("Error: ANTHROPIC_API_KEY environment variable not set (required for mode=claude)", file=sys.stderr)
            print("Set it with: export ANTHROPIC_API_KEY='your-key-here'", file=sys.stderr)
            print("Or pass with: --api-key YOUR_KEY", file=sys.stderr)
            sys.exit(1)
        elif args.mode == 'gemini' and not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set (required for mode=gemini)", file=sys.stderr)
            print("Set it with: export GOOGLE_API_KEY='your-key-here'", file=sys.stderr)
            print("Or pass with: --api-key YOUR_KEY", file=sys.stderr)
            sys.exit(1)
    else:
        # In OCR-only mode, no API key needed
        api_key = None

    if not os.path.exists(args.directory):
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.directory):
        print(f"Error: Not a directory: {args.directory}", file=sys.stderr)
        sys.exit(1)

    # Confirm overwrite mode (unless --yes)
    if args.overwrite and not args.yes:
        print("⚠️  WARNING: --overwrite mode will REPLACE original PDF files!")
        response = input("Are you sure? Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()

    try:
        batch_process(
            args.directory,
            api_key,
            overwrite=args.overwrite,
            skip_existing=not args.no_skip,
            auto_confirm=args.yes,
            mode=args.mode,
            output_format=args.format,
            ocr_only=args.ocr_only,
            skip_ocr=args.skip_ocr
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)


if __name__ == '__main__':
    main()

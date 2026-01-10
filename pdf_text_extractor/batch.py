"""
Command-line interface for batch processing PDFs.
"""

import sys
import os
from pathlib import Path
import fitz  # PyMuPDF
from .extractor import extract_pdf_text_with_mode, contains_api_error
from .injector import inject_text_to_pdf


def find_pdfs(directory):
    """Recursively find all PDF files in directory."""
    path = Path(directory)
    return sorted(path.rglob("*.pdf"))


def estimate_cost(pdf_files, skip_existing=True):
    """
    Estimate the cost of processing PDFs.

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

    # Cost calculation: $3 per 1000 input tokens, ~750 tokens per page (image)
    # Plus $15 per 1M output tokens, ~500 tokens output per page
    # Approximate: $0.003 per page all-in
    cost_per_page = 0.003
    estimated_cost = total_pages * cost_per_page

    return total_pdfs, len(pdfs_to_process), pdfs_with_errors, total_pages, estimated_cost


def batch_process(directory, api_key, overwrite=False, skip_existing=True, auto_confirm=False, mode='claude'):
    """
    Batch process all PDFs in a directory tree.

    Args:
        directory: Root directory to search
        api_key: Anthropic API key
        overwrite: If True, overwrite original PDFs. If False, create *_searchable.pdf
        skip_existing: If True, skip PDFs that already have text files
        auto_confirm: If True, skip confirmation prompt
    """

    pdf_files = find_pdfs(directory)

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return

    # Estimate cost
    total_pdfs, pdfs_to_process, pdfs_with_errors, total_pages, estimated_cost = estimate_cost(pdf_files, skip_existing)

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
    print(f"Estimated cost:          ${estimated_cost:.2f}")
    print()
    print(f"Mode: {'OVERWRITE originals' if overwrite else 'Create new files (*_searchable.pdf)'}")
    print(f"Skip existing: {'Yes' if skip_existing else 'No'}")
    print(f"Extraction mode: {mode}")
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
            response = input(f"Process {pdfs_to_process} PDFs (~${estimated_cost:.2f})? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Cancelled.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return
        print()
    else:
        print(f"Auto-confirming: Processing {pdfs_to_process} PDFs (~${estimated_cost:.2f})")
        print()

    processed = 0
    skipped = 0
    errors = 0

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_file.relative_to(directory)}")

        # Determine output paths
        txt_file = pdf_file.with_suffix('.txt')

        if overwrite:
            # Create temp file, then replace original
            output_pdf = pdf_file.with_suffix('.pdf.tmp')
            final_pdf = pdf_file
        else:
            # Create new file with _searchable suffix
            output_pdf = pdf_file.with_stem(f"{pdf_file.stem}_searchable")
            final_pdf = output_pdf

        # Check if already processed
        if skip_existing and txt_file.exists():
            # Check if the text file contains API errors
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if contains_api_error(content):
                    # File has errors, reprocess it
                    print(f"  ⚠ Reprocessing (API error detected in existing text file)")
                else:
                    # File is good, skip it
                    print(f"  ⊙ Skipping (text file exists)")
                    skipped += 1
                    continue
            except Exception:
                # Can't read file, better to reprocess
                print(f"  ⚠ Reprocessing (cannot read existing text file)")

        if skip_existing and final_pdf.exists() and final_pdf != pdf_file:
            print(f"  ⊙ Skipping (searchable PDF exists)")
            skipped += 1
            continue

        try:
            # Extract text
            print(f"  → Extracting text...")

            def progress(page, total):
                print(f"    Page {page}/{total}", end='\r', flush=True)

            extract_pdf_text_with_mode(str(pdf_file), str(txt_file), api_key=api_key, progress_callback=progress, mode=mode)
            print(f"  ✓ Text extracted: {txt_file.name}                    ")

            # Inject into PDF
            print(f"  → Creating searchable PDF...")
            inject_text_to_pdf(str(pdf_file), str(output_pdf), str(txt_file))

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


def main():
    """Main CLI entry point for pdf-batch command."""

    import argparse

    parser = argparse.ArgumentParser(
        description='Batch process PDFs with vision-based text extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process all PDFs, create new *_searchable.pdf files
  pdf-batch /path/to/pdfs

  # Overwrite original PDFs with searchable versions
  pdf-batch --overwrite /path/to/pdfs

  # Reprocess everything, even if text files exist
  pdf-batch --no-skip /path/to/pdfs

  # Skip confirmation prompt (auto-confirm)
  pdf-batch --yes /path/to/pdfs

Environment Variables:
  ANTHROPIC_API_KEY    Required. Your Anthropic API key.
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
        choices=['claude', 'spacy', 'local'],
        default='claude',
        help='Extraction mode: "claude" (default) uses Anthropic; "spacy" uses local layout/OCR tools'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt (auto-confirm)'
    )

    args = parser.parse_args()

    # Get API key (only required for Claude mode)
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')

    if args.mode == 'claude' and not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set (required for mode=claude)", file=sys.stderr)
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'", file=sys.stderr)
        print("Or pass with: --api-key YOUR_KEY", file=sys.stderr)
        sys.exit(1)

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
            mode=args.mode
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)


if __name__ == '__main__':
    main()

"""
Inject extracted text into PDFs as searchable layers.
"""

import fitz  # PyMuPDF


def inject_text_to_pdf(input_pdf, output_pdf, text_file):
    """
    Create a searchable PDF by adding invisible text layer.

    Args:
        input_pdf: Path to input PDF (scanned, no text layer)
        output_pdf: Path to output PDF (with searchable text)
        text_file: Path to text file with page markers (=== PAGE N ===)
    """

    # Read the text file with page markers
    with open(text_file, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # Split by page markers
    pages_text = []
    current_page_text = []

    for line in full_text.split('\n'):
        if line.startswith('=== PAGE'):
            if current_page_text:
                pages_text.append('\n'.join(current_page_text))
            current_page_text = []
        else:
            current_page_text.append(line)

    if current_page_text:
        pages_text.append('\n'.join(current_page_text))

    # Open input PDF
    doc = fitz.open(input_pdf)

    # For each page, add the text as invisible annotations
    for i, page in enumerate(doc):
        if i < len(pages_text):
            text = pages_text[i].strip()

            # Add text as hidden layer using PDF text rendering mode
            # Mode 3 = neither fill nor stroke (invisible)
            rect = page.rect

            # Insert text in tiny font with rendering mode 3 (invisible)
            # This makes it searchable but not visible
            fontsize = 1
            opacity = 0

            # Split into words and place them across the page
            words = text.split()
            x, y = 10, rect.height - 10
            line_words = []

            for word in words:
                # Add word to current line
                line_words.append(word)
                line = ' '.join(line_words)

                # Check if we need to wrap
                if len(line) * fontsize * 0.5 > rect.width - 20:
                    # Insert line and move to next
                    if len(line_words) > 1:
                        line = ' '.join(line_words[:-1])
                        page.insert_text((x, y), line, fontsize=fontsize,
                                       color=(0, 0, 0), render_mode=3)
                        line_words = [word]
                        y += fontsize * 1.2

                    # Check if we've filled the page
                    if y > rect.height - 10:
                        break

            # Insert remaining text
            if line_words:
                line = ' '.join(line_words)
                page.insert_text((x, y), line, fontsize=fontsize,
                               color=(0, 0, 0), render_mode=3)

    # Save with embedded text
    num_pages = len(doc)
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()

    return num_pages

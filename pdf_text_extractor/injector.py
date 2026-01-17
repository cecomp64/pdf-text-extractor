"""
Inject extracted text into PDFs as searchable layers using spaCy Layout OCR.
"""

import fitz  # PyMuPDF


def inject_text_to_pdf(input_pdf, output_pdf):
    """
    Create a searchable PDF by adding invisible text layer using OCR.

    This function uses spaCy Layout to OCR the PDF and extract word positions,
    then injects invisible text at those exact positions for accurate search highlighting.

    Args:
        input_pdf: Path to input PDF (scanned, no text layer)
        output_pdf: Path to output PDF (with searchable text)
    """

    # Load spaCy and spaCy Layout for OCR
    try:
        import spacy
        from spacy_layout import spaCyLayout
    except ImportError:
        raise ImportError(
            "pdf-inject requires spacy-layout. Install with: pip install -e '.[local]' && "
            "python -m spacy download en_core_web_sm"
        )

    # Open input PDF
    doc = fitz.open(input_pdf)

    # Load spaCy model and process entire PDF with spaCy Layout
    nlp = spacy.load("en_core_web_sm")
    layout_extractor = spaCyLayout(nlp)
    ocr_doc = layout_extractor(input_pdf)

    # For each page, clear existing text and inject OCR-positioned text
    for i, page in enumerate(doc):
        # Create a new page from just the images (removes all text)
        # Get the page's image content as pixmap
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution

        # Create a new PDF from this image
        temp_doc = fitz.open()
        temp_page = temp_doc.new_page(width=page.rect.width, height=page.rect.height)

        # Insert the pixmap as image
        temp_page.insert_image(page.rect, pixmap=pix)

        # Replace the current page with the cleaned page
        doc.delete_page(i)
        doc.insert_pdf(temp_doc, from_page=0, to_page=0, start_at=i)
        temp_doc.close()

        # Get the newly inserted page
        page = doc[i]

        # Use OCR word positions for accurate text placement
        # Filter tokens for current page
        for token in ocr_doc:
            # Check if token belongs to current page
            if hasattr(token, 'page') and token.page == i + 1:  # Pages are 1-indexed in spacy-layout
                if hasattr(token, 'x0') and hasattr(token, 'y0') and token.text.strip():
                    # Get bounding box from OCR
                    x0, y0, x1, y1 = token.x0, token.y0, token.x1, token.y1

                    # Calculate font size from bounding box height
                    bbox_height = y1 - y0
                    fontsize = max(6, bbox_height * 0.75)

                    # Insert invisible text at the word's position
                    try:
                        page.insert_text(
                            (x0, y1),  # Bottom-left corner of text
                            token.text,
                            fontsize=fontsize,
                            color=(0, 0, 0),
                            render_mode=3  # Invisible
                        )
                    except Exception:
                        # Skip if insertion fails
                        pass

    # Save with embedded text
    num_pages = len(doc)
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()

    return num_pages

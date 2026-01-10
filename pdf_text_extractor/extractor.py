"""
Core text extraction functionality using Claude's vision capabilities.
"""

import base64
from anthropic import Anthropic
import fitz  # PyMuPDF
import sys


def pdf_to_images(pdf_path):
    """Convert PDF pages to base64-encoded images."""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Render page to image (PNG) at 2x resolution for better quality
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = pix.pil_tobytes(format="PNG")

        # Encode to base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        images.append(img_base64)

    doc.close()
    return images


def extract_text_from_page(client, image_base64, page_num):
    """Use Claude to extract text from a single page image."""

    prompt = """Please extract all the text from this scanned document page.

Rules:
- Preserve the original formatting as much as possible
- Maintain paragraph breaks and line breaks
- Include all text exactly as it appears
- Do not add any commentary or explanations
- Just output the raw text content

Text:"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Extract text from response
        text = message.content[0].text

        # Clean up any "Text:" prefix if Claude added it
        if text.startswith("Text:"):
            text = text[5:].strip()

        return text

    except Exception as e:
        return f"[Error extracting page {page_num + 1}: {e}]"


def extract_pdf_text(pdf_path, output_path, api_key, progress_callback=None):
    return extract_pdf_text_with_mode(pdf_path, output_path, api_key=api_key, progress_callback=progress_callback, mode='claude')


def extract_pdf_text_with_mode(pdf_path, output_path, api_key=None, progress_callback=None, mode='claude'):
    """
    Extract text from PDF using different modes.

    mode: 'claude' (default) or 'spacy'/'local' (layout-based extraction using spacy-layout)
    If mode == 'claude', `api_key` must be provided. If mode == 'spacy'/'local', no API key is required.
    The spacy mode uses the spacy-layout library with the en_core_web_sm model for layout-aware
    text extraction from PDFs, including support for scanned documents via integrated OCR.
    """

    mode = (mode or 'claude').lower()

    all_text = []

    if mode == 'claude':
        if not api_key:
            raise ValueError('api_key is required when mode="claude"')

        # Convert PDF to images for Claude vision API
        images = pdf_to_images(pdf_path)
        total_pages = len(images)

        # Initialize Claude client
        client = Anthropic(api_key=api_key)

        for i, img_base64 in enumerate(images):
            if progress_callback:
                progress_callback(i + 1, total_pages)

            text = extract_text_from_page(client, img_base64, i)
            all_text.append(f"=== PAGE {i + 1} ===\n{text}")

    elif mode in ('spacy', 'local'):
        # Use spacy-layout for PDF text extraction with layout awareness
        try:
            import spacy
            from spacy_layout import spaCyLayout

            nlp = spacy.load("en_core_web_sm")
            layout = spaCyLayout(nlp)

            # Process the entire PDF with spaCyLayout
            doc = layout(pdf_path)

            # Get total pages for progress tracking
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)
            pdf_doc.close()

            # Extract text, preserving page structure
            # spaCyLayout processes the whole document, so we need to split by pages
            full_text = doc.text

            # If the document has page breaks or we can identify pages
            # For now, we'll treat it as a single extraction and format it
            if progress_callback:
                for i in range(total_pages):
                    progress_callback(i + 1, total_pages)

            # Since spaCyLayout returns a single doc, we format it as one page
            # or split by detected page boundaries if available
            all_text.append(f"=== DOCUMENT ===\n{full_text}")

        except ImportError as e:
            raise ImportError(
                "spacy-layout is required for local mode. Install with:\n"
                "  pip install spacy-layout\n"
                "  python -m spacy download en_core_web_sm"
            ) from e
        except Exception as e:
            all_text.append(f"[Error extracting text: {e}]")

    else:
        raise ValueError(f'Unknown extraction mode: {mode}')

    # Write output
    output_text = "\n\n".join(all_text)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    return total_pages

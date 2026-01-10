"""
Core text extraction functionality using Claude's vision capabilities.
"""

import base64
from anthropic import Anthropic
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
import base64 as _base64
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

    mode: 'claude' (default) or 'spacy' (local spaCy/layout-based OCR)
    If mode == 'claude', `api_key` must be provided. If mode == 'spacy', no API key is required,
    but optional local OCR/layout libraries improve results.
    """

    mode = (mode or 'claude').lower()

    # Convert PDF to images
    images = pdf_to_images(pdf_path)
    total_pages = len(images)

    all_text = []

    if mode == 'claude':
        if not api_key:
            raise ValueError('api_key is required when mode="claude"')

        # Initialize Claude client
        client = Anthropic(api_key=api_key)

        for i, img_base64 in enumerate(images):
            if progress_callback:
                progress_callback(i + 1, total_pages)

            text = extract_text_from_page(client, img_base64, i)
            all_text.append(f"=== PAGE {i + 1} ===\n{text}")

    elif mode in ('spacy', 'local'):
        # Try to use layoutparser/spacy/pytesseract if available, else fall back to PyMuPDF's text extraction
        try:
            import pytesseract
            have_pytesseract = True
        except Exception:
            have_pytesseract = False

        try:
            import layoutparser as lp  # optional
            have_layoutparser = True
        except Exception:
            have_layoutparser = False

        for i, img_base64 in enumerate(images):
            if progress_callback:
                progress_callback(i + 1, total_pages)

            # Decode image
            img_bytes = _base64.b64decode(img_base64)
            img = Image.open(BytesIO(img_bytes)).convert('RGB')

            page_text = None

            # Preferred approach: try layoutparser + pytesseract (if available)
            if have_layoutparser and have_pytesseract:
                try:
                    # Use layoutparser to detect text regions and pytesseract to OCR them
                    # Note: layoutparser models and OCR backends are optional; if this block
                    # fails, we fall back to pytesseract on the full image below.
                    lp_model = lp.Detectron2LayoutModel('lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config')
                    layout = lp_model.detect(img)
                    # If layoutparser returns regions, OCR each region and join
                    texts = []
                    for block in layout:
                        x1, y1, x2, y2 = map(int, [block.block.x1, block.block.y1, block.block.x2, block.block.y2])
                        region = img.crop((x1, y1, x2, y2))
                        texts.append(pytesseract.image_to_string(region))
                    page_text = "\n".join(t.strip() for t in texts if t and t.strip())
                except Exception:
                    page_text = None

            elif have_pytesseract:
                try:
                    page_text = pytesseract.image_to_string(img)
                except Exception:
                    page_text = None

            # Ultimate fallback: try PyMuPDF's builtin text extraction directly from the PDF
            if not page_text:
                try:
                    doc = fitz.open(pdf_path)
                    # Extract text for page i
                    page = doc[i]
                    page_text = page.get_text("text")
                    doc.close()
                except Exception as e:
                    page_text = f"[Error extracting page {i + 1}: {e}]"

            all_text.append(f"=== PAGE {i + 1} ===\n{page_text}")

    else:
        raise ValueError(f'Unknown extraction mode: {mode}')

    # Write output
    output_text = "\n\n".join(all_text)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    return total_pages

"""
Core text extraction functionality using Claude's vision capabilities.
"""

import base64
from anthropic import Anthropic
import fitz  # PyMuPDF


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
    """
    Extract text from PDF using Claude's vision capabilities.

    Args:
        pdf_path: Path to input PDF
        output_path: Path to output text file
        api_key: Anthropic API key
        progress_callback: Optional callback function(page_num, total_pages)
    """

    # Initialize Claude client
    client = Anthropic(api_key=api_key)

    # Convert PDF to images
    images = pdf_to_images(pdf_path)
    total_pages = len(images)

    all_text = []

    for i, img_base64 in enumerate(images):
        if progress_callback:
            progress_callback(i + 1, total_pages)

        text = extract_text_from_page(client, img_base64, i)
        all_text.append(f"=== PAGE {i + 1} ===\n{text}")

    # Write output
    output_text = "\n\n".join(all_text)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    return total_pages

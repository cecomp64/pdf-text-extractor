"""
Core text extraction functionality using vision AI (Claude or Gemini).
"""

import base64
from anthropic import Anthropic
import fitz  # PyMuPDF
import sys
import re
import os
import time


def contains_api_error(text):
    """
    Check if text contains API error messages.

    Returns True if an API error is detected, False otherwise.
    """
    if not text:
        return False

    # Check for error patterns
    error_patterns = [
        r'\[Error extracting page \d+:.*Error code:.*\]',
        r'Error code: \d+',
        r'invalid_request_error',
        r'authentication_error',
        r'permission_error',
        r'rate_limit_error',
        r'api_error',
        r'overloaded_error',
        r'credit balance is too low',
        r'Your credit balance is too low to access the Anthropic API',
    ]

    for pattern in error_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


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


def extract_text_from_page_gemini(client, image_base64, page_num, output_format='markdown'):
    """
    Use Gemini to extract text from a single page image.

    Args:
        client: Google GenerativeAI model
        image_base64: Base64-encoded image
        page_num: Page number (0-indexed)
        output_format: 'markdown' (default) or 'plain'
    """

    if output_format == 'markdown':
        prompt = """You are a precise document transcription tool. Extract all text from this scanned document page and output it as properly formatted markdown.

CRITICAL FORMATTING RULES:
1. Analyze visual hierarchy (font size, weight, position) to determine heading levels
2. Use markdown heading syntax strictly:
   - # for main/title headings (largest font)
   - ## for section headings (second largest)
   - ### for subsection headings (third largest)
   - And so on for smaller headings
3. Format lists correctly:
   - Use * or - for unordered lists
   - Use 1. 2. 3. for ordered/numbered lists
   - Maintain proper indentation for nested lists
4. Use **bold** for any visually emphasized or bold text
5. Use *italic* for any italicized text
6. Format tables using proper markdown table syntax with | separators and alignment
7. Use ``` for code blocks if any code is present
8. Use > for blockquotes if applicable
9. Maintain paragraph breaks with blank lines between paragraphs
10. Preserve the exact text content - no changes, additions, or omissions

OUTPUT REQUIREMENTS:
- Output ONLY the markdown-formatted text
- Do NOT include explanations, commentary, or meta-text
- Do NOT prefix with "Text:" or similar labels
- Start directly with the content

Begin extraction:"""
    else:
        prompt = """Please extract all the text from this scanned document page.

Rules:
- Preserve the original formatting as much as possible
- Maintain paragraph breaks and line breaks
- Include all text exactly as it appears
- Do not add any commentary or explanations
- Just output the raw text content

Text:"""

    try:
        from PIL import Image
        import io
        import warnings

        # Decode base64 image
        img_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(img_data))

        # Generate content using new google-genai API
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=[prompt, image]
        )

        # Extract text from response, suppressing non-text parts warning
        # Gemini may include inline_data parts which we don't need for text extraction
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*non-text parts.*")
            text = response.text

        # Clean up any "Text:" prefix if Gemini added it
        if text.startswith("Text:"):
            text = text[5:].strip()

        return text

    except Exception as e:
        return f"[Error extracting page {page_num + 1}: {e}]"


def extract_text_from_page(client, image_base64, page_num, output_format='markdown'):
    """
    Use Claude to extract text from a single page image.

    Args:
        client: Anthropic client
        image_base64: Base64-encoded image
        page_num: Page number (0-indexed)
        output_format: 'markdown' (default) or 'plain'
    """

    if output_format == 'markdown':
        prompt = """Please extract all the text from this scanned document page and format it as markdown.

Rules:
- Output the content in markdown format
- Preserve the document structure (headings, sections, lists, etc.)
- Use appropriate markdown syntax:
  * # for main headings, ## for subheadings, ### for sub-subheadings, etc.
  * - or * for bullet points
  * 1. 2. 3. for numbered lists
  * **bold** for emphasized text if applicable
  * Tables should use markdown table syntax if present
  * Code blocks with ``` if code is present
  * > for blockquotes if applicable
- Maintain paragraph breaks with blank lines between paragraphs
- Include all text exactly as it appears
- Infer the document structure from visual cues (font size, weight, indentation, etc.)
- Do not add any commentary or explanations
- Just output the formatted markdown content

Text:"""
    else:
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


def extract_pdf_text_with_mode(pdf_path, output_path, api_key=None, progress_callback=None, mode='claude', output_format='markdown', provider='claude'):
    """
    Extract text from PDF using different modes.

    Args:
        pdf_path: Path to input PDF
        output_path: Path to output file (will contain markdown by default)
        api_key: API key (Anthropic for Claude, Google for Gemini)
        progress_callback: Optional callback function for progress updates
        mode: 'claude' (default), 'gemini', or 'spacy'/'local' (layout-based extraction)
        output_format: 'markdown' (default) or 'plain' - controls the extraction format
        provider: 'claude' (default) or 'gemini' - which AI provider to use

    mode: 'claude' (default), 'gemini', or 'spacy'/'local' (layout-based extraction using spacy-layout)
    If mode in ('claude', 'gemini'), `api_key` must be provided. If mode == 'spacy'/'local', no API key is required.
    The spacy mode uses the spacy-layout library with the en_core_web_sm model for layout-aware
    text extraction from PDFs, including support for scanned documents via integrated OCR.

    Returns:
        tuple: (total_pages, page_timings, total_time) where page_timings is a list of (page_num, time_seconds)
    """

    mode = (mode or 'claude').lower()
    output_format = (output_format or 'markdown').lower()
    provider = (provider or 'claude').lower()

    # For backward compatibility: mode can also specify provider
    if mode in ('claude', 'gemini'):
        provider = mode
        mode = provider  # Keep mode in sync

    all_text = []
    page_timings = []  # Track timing for each page
    start_time = time.time()

    if mode == 'claude' or provider == 'claude':
        if not api_key:
            raise ValueError('api_key is required when mode="claude"')

        # Convert PDF to images for Claude vision API
        images = pdf_to_images(pdf_path)
        total_pages = len(images)

        # Initialize Claude client
        client = Anthropic(api_key=api_key)

        for i, img_base64 in enumerate(images):
            page_start = time.time()

            if progress_callback:
                progress_callback(i + 1, total_pages)

            text = extract_text_from_page(client, img_base64, i, output_format=output_format)
            all_text.append(f"=== PAGE {i + 1} ===\n{text}")

            page_time = time.time() - page_start
            page_timings.append((i + 1, page_time))

            # Check for API errors after each page
            if contains_api_error(text):
                raise RuntimeError(f"API error detected on page {i + 1}. Stopping extraction to prevent incomplete results. Error: {text}")

    elif mode == 'gemini' or provider == 'gemini':
        if not api_key:
            raise ValueError('api_key is required when mode="gemini"')

        # Convert PDF to images for Gemini vision API
        images = pdf_to_images(pdf_path)
        total_pages = len(images)

        # Initialize Gemini client with new google-genai SDK
        from google import genai
        client = genai.Client(api_key=api_key)

        for i, img_base64 in enumerate(images):
            page_start = time.time()

            if progress_callback:
                progress_callback(i + 1, total_pages)

            text = extract_text_from_page_gemini(client, img_base64, i, output_format=output_format)
            all_text.append(f"=== PAGE {i + 1} ===\n{text}")

            page_time = time.time() - page_start
            page_timings.append((i + 1, page_time))

            # Check for API errors after each page
            if contains_api_error(text):
                raise RuntimeError(f"API error detected on page {i + 1}. Stopping extraction to prevent incomplete results. Error: {text}")

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

    total_time = time.time() - start_time
    return total_pages, page_timings, total_time

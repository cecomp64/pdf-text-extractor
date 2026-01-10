from ollama_ocr import OCRProcessor

# Initialize OCR processor
#ocr = OCRProcessor(model_name='llama3.2-vision:11b', base_url="http://localhost:11434/api/generate")  # You can use any vision model available on Ollama
ocr = OCRProcessor(model_name='Granite3.2-vision', base_url="http://localhost:11434/api/generate")  # You can use any vision model available on Ollama
# you can pass your custom ollama api

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
- You *MUST* include all text, do not omit any sections
"""

# Process an image
result = ocr.process_image(
    image_path="/Users/csvensson/Git/pdf-text-extractor/examples/samples/Misc_80.pdf", # path to your pdf files "path/to/your/file.pdf"
    format_type="markdown",  # Options: markdown, text, json, structured, key_value
    custom_prompt=prompt, # Optional custom prompt
    language="English" # Specify the language of the text (New! 🆕)
)
print(result)
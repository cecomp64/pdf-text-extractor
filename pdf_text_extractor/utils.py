"""
Utility functions shared across the package.
"""

import re


def markdown_to_plain_text(markdown_text):
    """
    Convert markdown formatted text to plain text.

    Removes markdown formatting while preserving the actual content.
    This is used to generate plain text for PDF injection from markdown output.

    Args:
        markdown_text: String containing markdown formatted text

    Returns:
        Plain text version with markdown syntax removed
    """
    text = markdown_text

    # Remove bold/italic (** and * and __)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # Bold italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)       # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)           # Italic
    text = re.sub(r'___(.+?)___', r'\1', text)         # Bold italic
    text = re.sub(r'__(.+?)__', r'\1', text)           # Bold
    text = re.sub(r'_(.+?)_', r'\1', text)             # Italic

    # Remove strikethrough
    text = re.sub(r'~~(.+?)~~', r'\1', text)

    # Remove inline code
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove links but keep text [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove images ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

    # Remove heading markers (# ## ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove blockquote markers
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^[\-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove list markers but preserve indentation
    text = re.sub(r'^(\s*?)[\*\-\+]\s+', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^(\s*?)\d+\.\s+', r'\1', text, flags=re.MULTILINE)

    # Remove code block markers
    text = re.sub(r'^```[^\n]*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)

    # Remove table formatting - convert to plain text
    # Keep the content but remove the pipe separators and alignment rows
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip table alignment rows (|---|---|)
        if re.match(r'^\s*\|[\s\-\|:]+\|\s*$', line):
            continue
        # Clean pipe separators from table rows
        if '|' in line and line.strip().startswith('|'):
            # Remove leading/trailing pipes and split
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            cleaned_lines.append('  '.join(cells))
        else:
            cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)

    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

"""Export service for converting HTML contracts to document formats.

Converts HTML contract content to .docx format using python-docx,
preserving formatting including headings, paragraphs, and lists.
"""

import io
import re
from pathlib import Path
from typing import Optional, Tuple

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


class ExportService:
    """Service for exporting contracts to various document formats.

    Currently supports:
    - DOCX (Microsoft Word) via python-docx
    """

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize export service.

        Args:
            output_dir: Optional directory for saving exported files.
        """
        self.output_dir = Path(output_dir) if output_dir else None

    def html_to_docx(
        self,
        html_content: str,
        filename: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """Convert HTML content to a DOCX document.

        Parses HTML structure and maps it to Word document elements:
        - <h1> -> Heading 1
        - <h2> -> Heading 2
        - <h3> -> Heading 3
        - <p> -> Normal paragraph
        - <ol>/<li> -> Numbered list items
        - <ul>/<li> -> Bullet list items
        - <strong>/<b> -> Bold text

        Args:
            html_content: HTML string to convert.
            filename: Optional output filename (without extension).

        Returns:
            Tuple of (docx_bytes, filename).
        """
        document = Document()

        # Set default font
        style = document.styles["Normal"]
        font = style.font
        font.name = "Times New Roman"
        font.size = Pt(12)

        # Parse and convert HTML elements
        self._parse_html_to_docx(html_content, document)

        # Save to bytes
        buffer = io.BytesIO()
        document.save(buffer)
        buffer.seek(0)

        output_filename = filename or "kontrak_draft"
        if not output_filename.endswith(".docx"):
            output_filename += ".docx"

        return buffer.getvalue(), output_filename

    def _parse_html_to_docx(self, html: str, document: Document) -> None:
        """Parse HTML and add elements to the Word document.

        Uses regex-based parsing for the expected HTML structure
        produced by the drafting service.

        Args:
            html: HTML content string.
            document: python-docx Document to populate.
        """
        # Remove the outer div wrapper if present
        html = re.sub(r'<div[^>]*>', '', html)
        html = html.replace('</div>', '')

        # Process line by line
        lines = html.split('\n')
        in_list = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Heading 1
            h1_match = re.match(r'<h1[^>]*>(.*?)</h1>', line, re.IGNORECASE | re.DOTALL)
            if h1_match:
                text = self._strip_tags(h1_match.group(1))
                para = document.add_heading(text, level=1)
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                continue

            # Heading 2
            h2_match = re.match(r'<h2[^>]*>(.*?)</h2>', line, re.IGNORECASE | re.DOTALL)
            if h2_match:
                text = self._strip_tags(h2_match.group(1))
                document.add_heading(text, level=2)
                continue

            # Heading 3
            h3_match = re.match(r'<h3[^>]*>(.*?)</h3>', line, re.IGNORECASE | re.DOTALL)
            if h3_match:
                text = self._strip_tags(h3_match.group(1))
                document.add_heading(text, level=3)
                continue

            # List items
            li_match = re.match(r'\s*<li[^>]*>(.*?)</li>', line, re.IGNORECASE | re.DOTALL)
            if li_match:
                text = self._strip_tags(li_match.group(1))
                para = document.add_paragraph(text, style='List Number')
                continue

            # Paragraphs
            p_match = re.match(r'<p[^>]*>(.*?)</p>', line, re.IGNORECASE | re.DOTALL)
            if p_match:
                text = self._strip_tags(p_match.group(1))
                if text:
                    para = document.add_paragraph()
                    self._add_formatted_text(para, p_match.group(1))
                continue

            # Skip list container tags
            if re.match(r'</?[ou]l[^>]*>', line, re.IGNORECASE):
                continue

            # Plain text (not wrapped in tags)
            plain_text = self._strip_tags(line)
            if plain_text and not line.startswith('<'):
                document.add_paragraph(plain_text)

    def _strip_tags(self, html: str) -> str:
        """Remove all HTML tags from text.

        Args:
            html: HTML string to strip.

        Returns:
            Plain text without HTML tags.
        """
        clean = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&#39;', "'")
        return clean.strip()

    def _add_formatted_text(self, paragraph, html_text: str) -> None:
        """Add formatted text to a paragraph, handling bold/italic tags.

        Args:
            paragraph: python-docx paragraph to add text to.
            html_text: HTML text that may contain formatting tags.
        """
        # Split by <strong> or <b> tags
        parts = re.split(r'(<strong>|</strong>|<b>|</b>)', html_text)

        is_bold = False
        for part in parts:
            if part in ('<strong>', '<b>'):
                is_bold = True
                continue
            elif part in ('</strong>', '</b>'):
                is_bold = False
                continue
            else:
                text = self._strip_tags(part)
                if text:
                    run = paragraph.add_run(text)
                    run.bold = is_bold

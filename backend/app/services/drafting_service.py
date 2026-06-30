"""Drafting service for orchestrating contract generation.

Combines RAG retrieval, prompt construction, LLM generation,
and output formatting into a cohesive drafting workflow.
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from app.models.schemas import DraftRequest, DraftResponse
from app.rag.prompts import build_drafting_prompt
from app.rag.retriever import RetrieverService
from app.services.llm_service import LLMService, PromptTooLargeError
from app.utils.text_processing import (
    extract_placeholders,
    highlight_unfilled_variables,
    replace_placeholders,
)


class DraftingService:
    """Service for orchestrating contract draft generation.

    Coordinates between RAG retrieval, LLM generation, and output formatting
    to produce complete contract drafts.
    """

    def __init__(
        self,
        retriever: Optional[RetrieverService] = None,
        llm_service: Optional[LLMService] = None,
    ):
        """Initialize drafting service.

        Args:
            retriever: RetrieverService instance for clause retrieval.
            llm_service: LLMService instance for LLM interactions.
        """
        self.retriever = retriever or RetrieverService()
        self.llm_service = llm_service or LLMService()

    async def generate_draft(self, request: DraftRequest) -> DraftResponse:
        """Generate a complete contract draft.

        Retrieves relevant clauses from ChromaDB, constructs prompts,
        calls LLM for generation, and formats the output as HTML.

        Uses clause-by-clause processing mode for more reliable output
        with smaller language models.

        Args:
            request: DraftRequest with template name, variables, and options.

        Returns:
            DraftResponse with HTML content and metadata.
        """
        start_time = time.time()

        # Step 1: Retrieve clauses from ChromaDB
        if request.include_optional:
            clauses = self.retriever.get_all_clauses_for_template(
                request.template_name
            )
        else:
            clauses = self.retriever.get_mandatory_clauses(
                request.template_name
            )

        if not clauses:
            elapsed = time.time() - start_time
            return DraftResponse(
                html_content="<p>No clauses found for the specified template.</p>",
                metadata={
                    "error": "No clauses found",
                    "template": request.template_name,
                    "processing_time_seconds": round(elapsed, 2),
                },
                unfilled_variables=[],
            )

        # Step 2: Format clauses for the prompt
        clauses_text = self._format_clauses_for_prompt(clauses)

        # Step 3: Identify all variables and which ones are filled
        all_variables = self._extract_all_variables(clauses)
        filled_variables = set(request.variables.keys())
        unfilled = [v for v in all_variables if v not in filled_variables]

        # Step 4: Try full-document LLM generation first (fastest with cloud APIs)
        html_content = ""
        llm_used = False
        llm_mode = "none"

        try:
            logger.info(
                "Attempting full-document generation with %d clauses",
                len(clauses),
            )
            full_html = await self.llm_service.generate_full_document(
                clauses=clauses,
                variables=request.variables,
            )
            if full_html and len(full_html) > 100:
                validation_ok = self._validate_output_completeness(
                    full_html, clauses
                )
                if validation_ok:
                    html_content = full_html
                    llm_used = True
                    llm_mode = "full_document"
                else:
                    logger.warning(
                        "Full-document output failed validation, "
                        "falling back to clause-by-clause mode"
                    )
        except PromptTooLargeError as exc:
            logger.warning(
                "Full-document prompt too large: %s. "
                "Falling back to clause-by-clause mode immediately.",
                exc,
            )
        except Exception as exc:
            logger.warning(
                "Full-document generation failed: %s. "
                "Falling back to clause-by-clause mode.",
                exc,
            )

        # Step 5: If full-document failed, try clause-by-clause
        if not llm_used:
            try:
                logger.info("Attempting clause-by-clause generation")
                llm_html = await self.llm_service.generate_clause_by_clause(
                    clauses=clauses,
                    variables=request.variables,
                )
                if llm_html and len(llm_html) > 100:
                    validation_ok = self._validate_output_completeness(
                        llm_html, clauses
                    )
                    if validation_ok:
                        html_content = llm_html
                        llm_used = True
                        llm_mode = "clause_by_clause"
                    else:
                        logger.warning(
                            "Clause-by-clause output failed validation, "
                            "falling back to template-fill"
                        )
            except Exception as exc:
                logger.warning(
                    "Clause-by-clause generation failed: %s. "
                    "Falling back to template-fill.",
                    exc,
                )

        # Step 6: Final fallback - direct variable fill without LLM
        if not llm_used:
            logger.info("Using direct template-fill fallback")
            html_content = self._direct_variable_fill(clauses, request.variables)

        elapsed = time.time() - start_time

        # Step 7: Highlight any remaining unfilled variables with yellow background
        html_content = highlight_unfilled_variables(html_content)

        metadata = {
            "template_name": request.template_name,
            "total_clauses": len(clauses),
            "variables_provided": len(request.variables),
            "variables_unfilled": len(unfilled),
            "include_optional": request.include_optional,
            "llm_used": llm_used,
            "llm_mode": llm_mode,
            "processing_time_seconds": round(elapsed, 2),
        }

        return DraftResponse(
            html_content=html_content,
            metadata=metadata,
            unfilled_variables=unfilled,
        )

    def _validate_output_completeness(
        self,
        html_output: str,
        clauses: List[Dict[str, Any]],
    ) -> bool:
        """Validate that all expected pasal are present in the output.

        Checks that the HTML output contains headings for all clauses
        that were requested.

        Args:
            html_output: The generated HTML content.
            clauses: The list of clauses that should be in the output.

        Returns:
            True if validation passes, False otherwise.
        """
        html_lower = html_output.lower()
        missing_count = 0

        for clause in clauses:
            meta = clause.get("metadata", {})
            pasal = meta.get("pasal_number", "")
            if pasal:
                # Check if the pasal number appears in the output
                if pasal.lower() not in html_lower:
                    missing_count += 1

        # Allow up to 20% missing (some clauses may not have pasal numbers)
        total = len(clauses)
        if total == 0:
            return True

        missing_ratio = missing_count / total
        if missing_ratio > 0.2:
            logger.warning(
                "Output validation: %d/%d pasal missing (%.0f%%)",
                missing_count,
                total,
                missing_ratio * 100,
            )
            return False

        return True

    def _format_clauses_for_prompt(
        self, clauses: List[Dict[str, Any]]
    ) -> str:
        """Format retrieved clauses into text for LLM prompt.

        Args:
            clauses: List of clause dictionaries from retriever.

        Returns:
            Formatted text string with all clauses.
        """
        parts = []
        for clause in clauses:
            meta = clause.get("metadata", {})
            pasal = meta.get("pasal_number", "")
            section = meta.get("section_name", "")
            doc = clause.get("document", "")

            header = f"--- {pasal}: {section} ---" if pasal else f"--- {section} ---"
            parts.append(f"{header}\n{doc}")

        return "\n\n".join(parts)

    def _extract_all_variables(
        self, clauses: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract all unique variable names from clauses.

        Args:
            clauses: List of clause dictionaries.

        Returns:
            List of unique variable names.
        """
        all_vars = set()
        for clause in clauses:
            meta = clause.get("metadata", {})
            vars_list = meta.get("variables_list", "")
            if vars_list:
                for v in vars_list.split(", "):
                    v = v.strip()
                    if v:
                        all_vars.add(v)
            # Also extract from document text
            doc = clause.get("document", "")
            placeholders = extract_placeholders(doc)
            all_vars.update(placeholders)

        return sorted(all_vars)

    def _direct_variable_fill(
        self,
        clauses: List[Dict[str, Any]],
        variables: Dict[str, str],
    ) -> str:
        """Directly fill variables in clause text without LLM.

        Creates professionally formatted HTML output matching PLN official
        contract format. Includes proper spacing, separators between Pasal
        sections, nested numbered lists, and justified text alignment.

        Args:
            clauses: List of clause dictionaries.
            variables: Variable name to value mapping.

        Returns:
            HTML string with filled variables and professional formatting.
        """
        import re

        html_parts = ['<div class="contract-document">']
        html_parts.append(
            '  <h1 style="text-align: center; font-size: 18px; '
            'font-weight: bold; margin-bottom: 24px;">'
            "KONTRAK HARGA SATUAN</h1>"
        )

        for idx, clause in enumerate(clauses):
            meta = clause.get("metadata", {})
            pasal = meta.get("pasal_number", "")
            section = meta.get("section_name", "")
            doc = clause.get("document", "")

            # Extract just the clause text from the formatted document
            clause_text = doc
            # Try to find the "Isi:" section
            if "Isi:" in doc:
                isi_start = doc.index("Isi:") + 4
                isi_end = (
                    doc.index("\nVariabel:") if "\nVariabel:" in doc else len(doc)
                )
                clause_text = doc[isi_start:isi_end].strip()

            # Replace placeholders with provided variables
            filled_text = replace_placeholders(clause_text, variables)

            # Add separator between Pasal sections (not before the first one)
            if idx > 0:
                html_parts.append(
                    '  <hr class="pasal-separator" style="border: none; '
                    'border-top: 1px solid #e0e0e0; margin: 20px 0;" />'
                )

            # Build HTML with proper heading structure
            if pasal:
                html_parts.append(
                    f'  <h2 style="font-size: 14px; font-weight: bold; '
                    f'margin-top: 24px; margin-bottom: 12px;">'
                    f"{pasal} - {section}</h2>"
                )
            elif section:
                html_parts.append(
                    f'  <h2 style="font-size: 14px; font-weight: bold; '
                    f'margin-top: 24px; margin-bottom: 12px;">'
                    f"{section}</h2>"
                )

            # Parse text into structured content with nested list support
            lines = filled_text.split("\n")
            content_blocks = self._parse_content_blocks(lines)
            html_parts.extend(content_blocks)

        # Add signing section at the end of the document
        html_parts.append('  <div class="signing-section" style="margin-top: 40px;">')
        html_parts.append('    <p>Demikian Perjanjian ini dibuat...</p>')
        html_parts.append(
            '    <div style="display: flex; justify-content: space-between; margin-top: 40px;">'
        )
        html_parts.append('      <div style="text-align: center; width: 45%;">')
        html_parts.append("        <p><strong>PIHAK PERTAMA</strong></p>")
        html_parts.append(
            '        <div class="signature-placeholder" style="height: 80px; '
            "border: 1px dashed #ccc; margin: 20px 0; display: flex; "
            'align-items: center; justify-content: center; color: #999;">'
            "[Klik untuk insert TTD]</div>"
        )
        html_parts.append("        <p>[Nama Pihak Pertama]</p>")
        html_parts.append("      </div>")
        html_parts.append('      <div style="text-align: center; width: 45%;">')
        html_parts.append("        <p><strong>PIHAK KEDUA</strong></p>")
        html_parts.append(
            '        <div class="signature-placeholder" style="height: 80px; '
            "border: 1px dashed #ccc; margin: 20px 0; display: flex; "
            'align-items: center; justify-content: center; color: #999;">'
            "[Klik untuk insert TTD]</div>"
        )
        html_parts.append("        <p>[Nama Pihak Kedua]</p>")
        html_parts.append("      </div>")
        html_parts.append("    </div>")
        html_parts.append("  </div>")

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _parse_content_blocks(self, lines: List[str]) -> List[str]:
        """Parse lines of text into structured HTML content blocks.

        Handles detection of numbered lists (1. 2. 3.), sub-items (a. b. c.),
        deep sub-items (1) 2) 3)), and plain paragraphs. Produces nested
        <ol> elements with proper type attributes and indentation.

        Args:
            lines: List of text lines to parse.

        Returns:
            List of HTML strings representing the content blocks.
        """
        import re

        html_blocks: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Detect line type
            line_type = self._detect_line_type(line)

            if line_type == "main_number":
                # Collect all consecutive main numbered items and their sub-items
                ol_items, i = self._collect_numbered_list(lines, i, "main_number")
                html_blocks.append(
                    '  <ol type="1" style="margin-left: 0; '
                    'padding-left: 20px; margin-bottom: 12px;">'
                )
                for item_text, sub_items in ol_items:
                    if sub_items:
                        html_blocks.append(
                            f'    <li style="margin-bottom: 8px; '
                            f'line-height: 1.6; text-align: justify;">'
                            f"{item_text}"
                        )
                        html_blocks.append(
                            '      <ol type="a" style="margin-left: 20px; '
                            'padding-left: 20px; margin-top: 4px;">'
                        )
                        for sub_text, deep_items in sub_items:
                            if deep_items:
                                html_blocks.append(
                                    f'        <li style="margin-bottom: 4px; '
                                    f'line-height: 1.6; text-align: justify;">'
                                    f"{sub_text}"
                                )
                                html_blocks.append(
                                    '          <ol type="1" style="'
                                    "list-style-type: decimal; "
                                    'margin-left: 20px; padding-left: 20px; '
                                    'margin-top: 4px;">'
                                )
                                for deep_text in deep_items:
                                    html_blocks.append(
                                        f'            <li style="margin-bottom: 4px; '
                                        f'line-height: 1.6; text-align: justify;">'
                                        f"{deep_text}</li>"
                                    )
                                html_blocks.append("          </ol>")
                                html_blocks.append("        </li>")
                            else:
                                html_blocks.append(
                                    f'        <li style="margin-bottom: 4px; '
                                    f'line-height: 1.6; text-align: justify;">'
                                    f"{sub_text}</li>"
                                )
                        html_blocks.append("      </ol>")
                        html_blocks.append("    </li>")
                    else:
                        html_blocks.append(
                            f'    <li style="margin-bottom: 8px; '
                            f'line-height: 1.6; text-align: justify;">'
                            f"{item_text}</li>"
                        )
                html_blocks.append("  </ol>")
            elif line_type == "sub_letter":
                # Sub-letter list appearing without a parent main number
                ol_items, i = self._collect_sub_letter_list(lines, i)
                html_blocks.append(
                    '  <ol type="a" style="margin-left: 20px; '
                    'padding-left: 20px; margin-bottom: 12px;">'
                )
                for item_text, deep_items in ol_items:
                    if deep_items:
                        html_blocks.append(
                            f'    <li style="margin-bottom: 4px; '
                            f'line-height: 1.6; text-align: justify;">'
                            f"{item_text}"
                        )
                        html_blocks.append(
                            '      <ol type="1" style="list-style-type: decimal; '
                            'margin-left: 20px; padding-left: 20px; margin-top: 4px;">'
                        )
                        for deep_text in deep_items:
                            html_blocks.append(
                                f'        <li style="margin-bottom: 4px; '
                                f'line-height: 1.6; text-align: justify;">'
                                f"{deep_text}</li>"
                            )
                        html_blocks.append("      </ol>")
                        html_blocks.append("    </li>")
                    else:
                        html_blocks.append(
                            f'    <li style="margin-bottom: 4px; '
                            f'line-height: 1.6; text-align: justify;">'
                            f"{item_text}</li>"
                        )
                html_blocks.append("  </ol>")
            else:
                # Plain paragraph
                html_blocks.append(
                    f'  <p style="margin-bottom: 12px; line-height: 1.6; '
                    f'text-align: justify;">{line}</p>'
                )
                i += 1

        return html_blocks

    def _detect_line_type(self, line: str) -> str:
        """Detect the type of a content line.

        Distinguishes between main numbered items (1. 2. 3.),
        sub-letter items (a. b. c.), deep sub-items (1) 2) 3)),
        and plain text.

        Args:
            line: The text line to classify.

        Returns:
            One of: 'main_number', 'sub_letter', 'deep_number', 'paragraph'.
        """
        import re

        if not line or len(line) < 2:
            return "paragraph"

        # Main number: starts with digit(s) followed by a period and space
        # e.g., "1. Item text", "12. Item text"
        if re.match(r"^\d+\.\s", line):
            return "main_number"

        # Sub-letter: starts with a single lowercase letter followed by . or )
        # e.g., "a. Sub item", "b) Sub item"
        if re.match(r"^[a-z][.)]\s", line):
            return "sub_letter"

        # Deep number: starts with digit(s) followed by ) and space
        # e.g., "1) Deep item", "2) Deep item"
        if re.match(r"^\d+\)\s", line):
            return "deep_number"

        return "paragraph"

    def _collect_numbered_list(
        self, lines: List[str], start_idx: int, expected_type: str
    ) -> tuple:
        """Collect consecutive numbered list items with their sub-items.

        Args:
            lines: All lines of text.
            start_idx: Index of the first numbered item.
            expected_type: The type of items to collect ('main_number').

        Returns:
            Tuple of (items_list, next_index) where items_list contains
            tuples of (item_text, sub_items_list).
        """
        import re

        items: List[tuple] = []
        i = start_idx

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            line_type = self._detect_line_type(line)

            if line_type == expected_type:
                # Extract the text after the number prefix
                item_text = re.sub(r"^\d+\.\s*", "", line)
                i += 1

                # Collect any sub-items (letters) belonging to this item
                sub_items: List[tuple] = []
                while i < len(lines):
                    sub_line = lines[i].strip()
                    if not sub_line:
                        i += 1
                        continue

                    sub_type = self._detect_line_type(sub_line)
                    if sub_type == "sub_letter":
                        sub_text = re.sub(r"^[a-z][.)]\s*", "", sub_line)
                        i += 1

                        # Collect deep sub-items belonging to this sub-item
                        deep_items: List[str] = []
                        while i < len(lines):
                            deep_line = lines[i].strip()
                            if not deep_line:
                                i += 1
                                continue
                            deep_type = self._detect_line_type(deep_line)
                            if deep_type == "deep_number":
                                deep_text = re.sub(r"^\d+\)\s*", "", deep_line)
                                deep_items.append(deep_text)
                                i += 1
                            else:
                                break

                        sub_items.append((sub_text, deep_items))
                    elif sub_type == "deep_number":
                        # Deep number directly under main item (no sub-letter parent)
                        deep_text = re.sub(r"^\d+\)\s*", "", sub_line)
                        # Attach as a sub-item with no deeper nesting
                        sub_items.append((deep_text, []))
                        i += 1
                    else:
                        break

                items.append((item_text, sub_items))
            else:
                break

        return items, i

    def _collect_sub_letter_list(
        self, lines: List[str], start_idx: int
    ) -> tuple:
        """Collect consecutive sub-letter list items with their deep sub-items.

        Args:
            lines: All lines of text.
            start_idx: Index of the first sub-letter item.

        Returns:
            Tuple of (items_list, next_index) where items_list contains
            tuples of (item_text, deep_items_list).
        """
        import re

        items: List[tuple] = []
        i = start_idx

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            line_type = self._detect_line_type(line)

            if line_type == "sub_letter":
                sub_text = re.sub(r"^[a-z][.)]\s*", "", line)
                i += 1

                # Collect deep sub-items
                deep_items: List[str] = []
                while i < len(lines):
                    deep_line = lines[i].strip()
                    if not deep_line:
                        i += 1
                        continue
                    deep_type = self._detect_line_type(deep_line)
                    if deep_type == "deep_number":
                        deep_text = re.sub(r"^\d+\)\s*", "", deep_line)
                        deep_items.append(deep_text)
                        i += 1
                    else:
                        break

                items.append((sub_text, deep_items))
            else:
                break

        return items, i

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
from app.services.llm_service import LLMService
from app.utils.text_processing import extract_placeholders, replace_placeholders


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

        Creates HTML output by assembling clauses and replacing placeholders.
        Uses proper heading numbering and paragraph structure.

        Args:
            clauses: List of clause dictionaries.
            variables: Variable name to value mapping.

        Returns:
            HTML string with filled variables.
        """
        html_parts = ['<div class="contract-document">']
        html_parts.append("  <h1>KONTRAK HARGA SATUAN</h1>")

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
                isi_end = doc.index("\nVariabel:") if "\nVariabel:" in doc else len(doc)
                clause_text = doc[isi_start:isi_end].strip()

            # Replace placeholders with provided variables
            filled_text = replace_placeholders(clause_text, variables)

            # Build HTML with proper heading structure
            if pasal:
                html_parts.append(f"  <h2>{pasal} - {section}</h2>")
            elif section:
                html_parts.append(f"  <h2>{section}</h2>")

            # Split text into paragraphs and handle numbering
            paragraphs = filled_text.split("\n")
            in_numbered_list = False
            numbered_items = []

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Detect numbered items (e.g., "1.", "2.", "a.", "b)")
                is_numbered = (
                    len(para) > 2
                    and (
                        (para[0].isdigit() and para[1] in ".)")
                        or (para[0].isalpha() and len(para) > 1 and para[1] in ".)")
                    )
                )

                if is_numbered:
                    if not in_numbered_list:
                        in_numbered_list = True
                        numbered_items = []
                    numbered_items.append(para)
                else:
                    # Flush any pending numbered list
                    if in_numbered_list:
                        html_parts.append("  <ol>")
                        for item in numbered_items:
                            # Remove the leading number/letter and delimiter
                            item_text = item.lstrip("0123456789abcdefghij.)")
                            item_text = item_text.strip()
                            html_parts.append(f"    <li>{item_text}</li>")
                        html_parts.append("  </ol>")
                        in_numbered_list = False
                        numbered_items = []

                    html_parts.append(f"  <p>{para}</p>")

            # Flush remaining numbered list
            if in_numbered_list and numbered_items:
                html_parts.append("  <ol>")
                for item in numbered_items:
                    item_text = item.lstrip("0123456789abcdefghij.)")
                    item_text = item_text.strip()
                    html_parts.append(f"    <li>{item_text}</li>")
                html_parts.append("  </ol>")

        html_parts.append("</div>")
        return "\n".join(html_parts)

"""Drafting service for orchestrating contract generation.

Combines RAG retrieval, prompt construction, LLM generation,
and output formatting into a cohesive drafting workflow.
"""

import logging
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

        Args:
            request: DraftRequest with template name, variables, and options.

        Returns:
            DraftResponse with HTML content and metadata.
        """
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
            return DraftResponse(
                html_content="<p>No clauses found for the specified template.</p>",
                metadata={"error": "No clauses found", "template": request.template_name},
                unfilled_variables=[],
            )

        # Step 2: Format clauses for the prompt
        clauses_text = self._format_clauses_for_prompt(clauses)

        # Step 3: Identify all variables and which ones are filled
        all_variables = self._extract_all_variables(clauses)
        filled_variables = set(request.variables.keys())
        unfilled = [v for v in all_variables if v not in filled_variables]

        # Step 4: Try to fill variables directly first (without LLM)
        html_content = self._direct_variable_fill(clauses, request.variables)

        # Step 5: If LLM is available, enhance the output
        llm_used = False
        try:
            llm_html = await self.llm_service.generate_draft(
                clauses_text=clauses_text,
                variables=request.variables,
            )
            if llm_html and len(llm_html) > 100:
                html_content = llm_html
                llm_used = True
        except Exception as exc:
            logger.warning(
                "LLM generation failed, falling back to template-fill: %s", exc
            )

        metadata = {
            "template_name": request.template_name,
            "total_clauses": len(clauses),
            "variables_provided": len(request.variables),
            "variables_unfilled": len(unfilled),
            "include_optional": request.include_optional,
            "llm_used": llm_used,
        }

        return DraftResponse(
            html_content=html_content,
            metadata=metadata,
            unfilled_variables=unfilled,
        )

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

        Args:
            clauses: List of clause dictionaries.
            variables: Variable name to value mapping.

        Returns:
            HTML string with filled variables.
        """
        html_parts = ['<div class="contract-document">']

        for clause in clauses:
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

            # Build HTML
            if pasal:
                html_parts.append(f'  <h2>{pasal} - {section}</h2>')
            elif section:
                html_parts.append(f'  <h2>{section}</h2>')

            # Split text into paragraphs
            paragraphs = filled_text.split("\n")
            for para in paragraphs:
                para = para.strip()
                if para:
                    html_parts.append(f'  <p>{para}</p>')

        html_parts.append('</div>')
        return "\n".join(html_parts)

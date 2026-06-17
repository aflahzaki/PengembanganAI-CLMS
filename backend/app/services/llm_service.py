"""LLM Service for interacting with LMStudio endpoint.

Provides async methods for calling the OpenAI-compatible LMStudio API
for contract drafting and variable filling operations.
"""

import json
import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.config import settings
from app.rag.prompts import LEGAL_DRAFTING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMResponseValidationError(Exception):
    """Raised when the LLM response fails validation checks."""

    pass


class LLMService:
    """Service for LLM interactions via LMStudio.

    Uses the OpenAI-compatible chat completions endpoint at LMStudio
    for generating contract drafts and filling variables.
    """

    # Default temperature for legal text generation (low for determinism)
    DEFAULT_TEMPERATURE = 0.1

    # Minimum acceptable response length (characters)
    MIN_RESPONSE_LENGTH = 50

    # HTML tags that should be present in a valid HTML response
    EXPECTED_HTML_TAGS = ["<h2", "<p"]

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """Initialize LLM service.

        Args:
            base_url: LLM API base URL. Defaults to config value.
            model_name: Model name for the API. Defaults to config value.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
        """
        self.base_url = base_url or settings.LLM_BASE_URL
        self.model_name = model_name or settings.LLM_MODEL_NAME
        self.timeout = timeout
        self.max_retries = max_retries
        self.chat_endpoint = f"{self.base_url}/chat/completions"

    def _validate_response(
        self,
        response_text: str,
        require_html: bool = True,
    ) -> str:
        """Validate LLM response meets quality requirements.

        Args:
            response_text: The raw response text from LLM.
            require_html: Whether to check for HTML tag presence.

        Returns:
            The validated response text (stripped).

        Raises:
            LLMResponseValidationError: If validation fails.
        """
        if not response_text:
            raise LLMResponseValidationError("LLM returned empty response")

        cleaned = response_text.strip()

        if len(cleaned) < self.MIN_RESPONSE_LENGTH:
            raise LLMResponseValidationError(
                f"LLM response too short: {len(cleaned)} chars "
                f"(minimum: {self.MIN_RESPONSE_LENGTH})"
            )

        if require_html:
            has_html_tags = any(
                tag in cleaned.lower() for tag in self.EXPECTED_HTML_TAGS
            )
            if not has_html_tags:
                raise LLMResponseValidationError(
                    "LLM response does not contain expected HTML tags "
                    f"(expected at least one of: {self.EXPECTED_HTML_TAGS})"
                )

        return cleaned

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = LEGAL_DRAFTING_SYSTEM_PROMPT,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
        require_html: bool = False,
    ) -> str:
        """Generate a completion from the LLM.

        Args:
            prompt: The user prompt/instruction.
            system_prompt: System prompt for context setting.
            temperature: Sampling temperature. Defaults to 0.1.
            max_tokens: Maximum tokens to generate.
            require_html: Whether to validate HTML presence in response.

        Returns:
            Generated text response.

        Raises:
            httpx.HTTPError: If the API request fails after retries.
            LLMResponseValidationError: If response fails validation.
        """
        if temperature is None:
            temperature = self.DEFAULT_TEMPERATURE

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.chat_endpoint,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    result = data["choices"][0]["message"]["content"]
                    return self._validate_response(
                        result, require_html=require_html
                    )
            except LLMResponseValidationError as e:
                logger.warning(
                    "LLM response validation failed (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    str(e),
                )
                last_error = e
                if attempt < self.max_retries - 1:
                    continue
            except (httpx.HTTPError, KeyError, IndexError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue

        raise last_error or Exception("LLM request failed after all retries")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_DRAFTING_SYSTEM_PROMPT,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming completion from the LLM.

        Args:
            prompt: The user prompt/instruction.
            system_prompt: System prompt for context setting.
            temperature: Sampling temperature. Defaults to 0.1.
            max_tokens: Maximum tokens to generate.

        Yields:
            Text chunks as they are generated.
        """
        if temperature is None:
            temperature = self.DEFAULT_TEMPERATURE

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST", self.chat_endpoint, json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    async def generate_draft(
        self,
        clauses_text: str,
        variables: Dict[str, str],
    ) -> str:
        """Generate a complete contract draft.

        Args:
            clauses_text: Formatted clause text from RAG retrieval.
            variables: Variable name to value mapping.

        Returns:
            Generated HTML contract content.
        """
        from app.rag.prompts import build_drafting_prompt

        prompt = build_drafting_prompt(
            clauses_text=clauses_text,
            variables_json=json.dumps(variables, ensure_ascii=False, indent=2),
        )
        return await self.generate_completion(prompt, require_html=True)

    async def generate_clause_by_clause(
        self,
        clauses: List[Dict[str, Any]],
        variables: Dict[str, str],
    ) -> str:
        """Generate contract HTML by processing each clause individually.

        This mode is more reliable for smaller models (8B parameters) as it
        processes one pasal at a time and concatenates the results.

        Args:
            clauses: List of clause dictionaries with metadata.
            variables: Variable name to value mapping.

        Returns:
            Concatenated HTML content of all processed clauses.
        """
        from app.rag.prompts import build_single_clause_prompt

        variables_json = json.dumps(variables, ensure_ascii=False, indent=2)
        html_parts = ['<div class="contract-document">']
        html_parts.append("<h1>KONTRAK HARGA SATUAN</h1>")

        for clause in clauses:
            meta = clause.get("metadata", {})
            pasal_number = meta.get("pasal_number", "")
            section_name = meta.get("section_name", "")
            doc = clause.get("document", "")

            # Extract clause text from the formatted document
            clause_text = doc
            if "Isi:" in doc:
                isi_start = doc.index("Isi:") + 4
                isi_end = (
                    doc.index("\nVariabel:")
                    if "\nVariabel:" in doc
                    else len(doc)
                )
                clause_text = doc[isi_start:isi_end].strip()

            prompt = build_single_clause_prompt(
                pasal_number=pasal_number,
                section_name=section_name,
                clause_text=clause_text,
                variables_json=variables_json,
            )

            try:
                clause_html = await self.generate_completion(
                    prompt, require_html=False
                )
                # Ensure it has at least a heading
                if f"<h2" not in clause_html.lower():
                    clause_html = (
                        f"<h2>{pasal_number} - {section_name}</h2>\n"
                        f"{clause_html}"
                    )
                html_parts.append(clause_html)
            except Exception as exc:
                logger.warning(
                    "Clause-by-clause generation failed for %s: %s",
                    pasal_number,
                    exc,
                )
                # Fallback: use template text directly with variable fill
                from app.utils.text_processing import replace_placeholders

                filled = replace_placeholders(clause_text, variables)
                html_parts.append(
                    f"<h2>{pasal_number} - {section_name}</h2>"
                )
                html_parts.append(f"<p>{filled}</p>")

        html_parts.append("</div>")
        return "\n".join(html_parts)

    async def fill_variables(
        self,
        clause_text: str,
        variables: Dict[str, str],
    ) -> str:
        """Fill variables in a specific clause.

        Args:
            clause_text: Clause text with placeholders.
            variables: Variable name to value mapping.

        Returns:
            Clause text with variables filled.
        """
        from app.rag.prompts import build_variable_filling_prompt

        prompt = build_variable_filling_prompt(
            clause_text=clause_text,
            variables_json=json.dumps(variables, ensure_ascii=False, indent=2),
        )
        return await self.generate_completion(prompt, require_html=False)

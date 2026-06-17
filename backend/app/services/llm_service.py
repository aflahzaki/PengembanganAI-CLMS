"""LLM Service for interacting with LMStudio endpoint.

Provides async methods for calling the OpenAI-compatible LMStudio API
for contract drafting and variable filling operations.
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.config import settings
from app.rag.prompts import LEGAL_DRAFTING_SYSTEM_PROMPT


class LLMService:
    """Service for LLM interactions via LMStudio.

    Uses the OpenAI-compatible chat completions endpoint at LMStudio
    for generating contract drafts and filling variables.
    """

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

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = LEGAL_DRAFTING_SYSTEM_PROMPT,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a completion from the LLM.

        Args:
            prompt: The user prompt/instruction.
            system_prompt: System prompt for context setting.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text response.

        Raises:
            httpx.HTTPError: If the API request fails after retries.
        """
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
                    return data["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, IndexError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    continue

        raise last_error or Exception("LLM request failed after all retries")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_DRAFTING_SYSTEM_PROMPT,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming completion from the LLM.

        Args:
            prompt: The user prompt/instruction.
            system_prompt: System prompt for context setting.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            Text chunks as they are generated.
        """
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
        return await self.generate_completion(prompt)

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
        return await self.generate_completion(prompt)

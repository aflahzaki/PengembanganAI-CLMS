"""Tests for the drafting service and related modules.

Tests schema validation, prompt construction, and text processing utilities.
"""

import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.models.schemas import (
    ClauseSchema,
    DraftRequest,
    DraftResponse,
    ExportRequest,
    TemplateInfo,
    VariableSchema,
)
from app.rag.prompts import (
    FULL_DOCUMENT_ASSEMBLY_PROMPT,
    LEGAL_DRAFTING_SYSTEM_PROMPT,
    build_drafting_prompt,
    build_full_document_prompt,
    build_variable_filling_prompt,
)
from app.utils.text_processing import (
    clean_legal_text,
    extract_placeholders,
    format_clause_for_embedding,
    replace_placeholders,
)


class TestTextProcessing:
    """Test suite for text processing utilities."""

    def test_extract_placeholders_basic(self) -> None:
        """Test basic placeholder extraction."""
        text = "Kontrak [Nomor Kontrak] tanggal [Tanggal]"
        result = extract_placeholders(text)
        assert result == ["Nomor Kontrak", "Tanggal"]

    def test_extract_placeholders_duplicates(self) -> None:
        """Test that duplicate placeholders are deduplicated."""
        text = "[Nama] dan [Nama] serta [Alamat]"
        result = extract_placeholders(text)
        assert result == ["Nama", "Alamat"]

    def test_extract_placeholders_empty(self) -> None:
        """Test with empty input."""
        assert extract_placeholders("") == []
        assert extract_placeholders(None) == []

    def test_extract_placeholders_no_matches(self) -> None:
        """Test with no placeholders."""
        text = "Teks tanpa placeholder apapun."
        assert extract_placeholders(text) == []

    def test_replace_placeholders_basic(self) -> None:
        """Test basic placeholder replacement."""
        text = "[Nama] dari [Perusahaan]"
        mapping = {"Nama": "Budi", "Perusahaan": "PT ABC"}
        result = replace_placeholders(text, mapping)
        assert result == "Budi dari PT ABC"

    def test_replace_placeholders_partial(self) -> None:
        """Test replacement when only some variables are provided."""
        text = "[Nama] dari [Perusahaan] di [Alamat]"
        mapping = {"Nama": "Budi"}
        result = replace_placeholders(text, mapping)
        assert "Budi" in result
        assert "[Perusahaan]" in result
        assert "[Alamat]" in result

    def test_replace_placeholders_empty_mapping(self) -> None:
        """Test with empty mapping."""
        text = "[Nama] test"
        result = replace_placeholders(text, {})
        assert result == "[Nama] test"

    def test_format_clause_for_embedding(self) -> None:
        """Test clause formatting for embedding."""
        result = format_clause_for_embedding(
            pasal_number="Pasal 1",
            section_name="DEFINISI",
            clause_text="Istilah dalam kontrak...",
            variables=["Nama", "Alamat"],
        )
        assert "Pasal 1" in result
        assert "DEFINISI" in result
        assert "Istilah dalam kontrak" in result
        assert "Nama" in result
        assert "Alamat" in result

    def test_clean_legal_text(self) -> None:
        """Test legal text cleaning."""
        text = "  Teks  dengan   banyak   spasi  \n\n\n\n dan baris kosong  "
        result = clean_legal_text(text)
        assert "  " not in result
        assert "\n\n\n" not in result
        assert result.startswith("Teks")

    def test_clean_legal_text_empty(self) -> None:
        """Test cleaning empty text."""
        assert clean_legal_text("") == ""
        assert clean_legal_text(None) == ""


class TestSchemas:
    """Test suite for Pydantic schemas."""

    def test_draft_request_defaults(self) -> None:
        """Test DraftRequest with default values."""
        request = DraftRequest()
        assert request.template_name == "KHS Material Ketenagalistrikan"
        assert request.variables == {}
        assert request.include_optional is True

    def test_draft_request_custom(self) -> None:
        """Test DraftRequest with custom values."""
        request = DraftRequest(
            template_name="Custom Template",
            variables={"Nama": "Test"},
            include_optional=False,
        )
        assert request.template_name == "Custom Template"
        assert request.variables == {"Nama": "Test"}
        assert request.include_optional is False

    def test_draft_response(self) -> None:
        """Test DraftResponse creation."""
        response = DraftResponse(
            html_content="<h1>Kontrak</h1>",
            metadata={"clauses": 5},
            unfilled_variables=["Nama"],
        )
        assert response.html_content == "<h1>Kontrak</h1>"
        assert response.metadata["clauses"] == 5
        assert "Nama" in response.unfilled_variables

    def test_export_request(self) -> None:
        """Test ExportRequest validation."""
        request = ExportRequest(
            html_content="<p>test</p>",
            format="docx",
        )
        assert request.html_content == "<p>test</p>"
        assert request.format == "docx"

    def test_variable_schema(self) -> None:
        """Test VariableSchema creation."""
        var = VariableSchema(
            name="Nomor Kontrak",
            description="Nomor unik kontrak",
            required=True,
        )
        assert var.name == "Nomor Kontrak"
        assert var.required is True

    def test_clause_schema(self) -> None:
        """Test ClauseSchema creation."""
        clause = ClauseSchema(
            pasal_number="Pasal 1",
            section_name="DEFINISI",
            clause_text="Teks klausul",
            variables=["Nama"],
            is_mandatory=True,
        )
        assert clause.pasal_number == "Pasal 1"
        assert len(clause.variables) == 1

    def test_template_info(self) -> None:
        """Test TemplateInfo creation."""
        info = TemplateInfo(
            name="KHS Material",
            description="Template KHS",
            clauses_count=45,
            mandatory_clauses=30,
            optional_clauses=15,
        )
        assert info.clauses_count == 45
        assert info.mandatory_clauses == 30


class TestPrompts:
    """Test suite for prompt templates."""

    def test_system_prompt_exists(self) -> None:
        """Test that system prompt is defined and non-empty."""
        assert LEGAL_DRAFTING_SYSTEM_PROMPT
        assert len(LEGAL_DRAFTING_SYSTEM_PROMPT) > 100

    def test_build_drafting_prompt(self) -> None:
        """Test drafting prompt construction."""
        prompt = build_drafting_prompt(
            clauses_text="Pasal 1: DEFINISI\nIstilah dalam kontrak...",
            variables_json='{"Nama": "PT ABC"}',
        )
        assert "Pasal 1" in prompt
        assert "PT ABC" in prompt

    def test_build_variable_filling_prompt(self) -> None:
        """Test variable filling prompt construction."""
        prompt = build_variable_filling_prompt(
            clause_text="[Nama] dari [Perusahaan]",
            variables_json='{"Nama": "Budi", "Perusahaan": "PT ABC"}',
        )
        assert "[Nama]" in prompt
        assert "Budi" in prompt


class TestConfig:
    """Test suite for application configuration."""

    def test_config_has_llm_api_key(self) -> None:
        """Test that settings has LLM_API_KEY field."""
        from app.config import Settings

        s = Settings(
            LLM_API_KEY="test-key",
            LLM_BASE_URL="https://api.deepseek.com/v1",
            LLM_MODEL_NAME="deepseek-chat",
        )
        assert s.LLM_API_KEY == "test-key"

    def test_config_defaults_deepseek(self) -> None:
        """Test that default config points to DeepSeek."""
        from app.config import Settings

        s = Settings(_env_file=None)
        assert "deepseek" in s.LLM_BASE_URL
        assert s.LLM_MODEL_NAME == "deepseek-chat"

    def test_config_api_key_default_empty(self) -> None:
        """Test that LLM_API_KEY defaults to empty string."""
        from app.config import Settings

        s = Settings(_env_file=None)
        assert s.LLM_API_KEY == ""

    def test_config_loaded_from_env(self) -> None:
        """Test that settings loads from .env file when present."""
        from app.config import settings

        # The .env file should be present with the DeepSeek API key
        assert settings.LLM_API_KEY != ""
        assert "deepseek" in settings.LLM_BASE_URL


class TestLLMServiceAuth:
    """Test suite for LLM service authentication and headers."""

    def test_get_headers_with_api_key(self) -> None:
        """Test that Authorization header is set when API key is provided."""
        from app.services.llm_service import LLMService

        service = LLMService(api_key="sk-test-key-123")
        headers = service._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer sk-test-key-123"
        assert headers["Content-Type"] == "application/json"

    def test_get_headers_without_api_key(self) -> None:
        """Test that Authorization header is absent when no API key."""
        from app.services.llm_service import LLMService

        service = LLMService(api_key="")
        headers = service._get_headers()
        assert "Authorization" not in headers
        assert "Content-Type" in headers

    def test_llm_service_default_temperature(self) -> None:
        """Test that default temperature is 0.3."""
        from app.services.llm_service import LLMService

        assert LLMService.DEFAULT_TEMPERATURE == 0.3

    def test_llm_service_default_timeout(self) -> None:
        """Test that default timeout is 180 seconds."""
        from app.services.llm_service import LLMService

        service = LLMService(api_key="test")
        assert service.timeout == 180.0

    def test_llm_service_uses_config_api_key(self) -> None:
        """Test that LLMService loads API key from config by default."""
        from app.services.llm_service import LLMService

        service = LLMService()
        # Should pick up from settings (loaded from .env)
        from app.config import settings

        assert service.api_key == settings.LLM_API_KEY

    def test_llm_service_custom_api_key_override(self) -> None:
        """Test that custom API key overrides config."""
        from app.services.llm_service import LLMService

        service = LLMService(api_key="custom-key-override")
        assert service.api_key == "custom-key-override"


class TestFullDocumentPrompt:
    """Test suite for full document assembly prompt."""

    def test_full_document_prompt_template_exists(self) -> None:
        """Test that FULL_DOCUMENT_ASSEMBLY_PROMPT is defined."""
        assert FULL_DOCUMENT_ASSEMBLY_PROMPT
        assert len(FULL_DOCUMENT_ASSEMBLY_PROMPT) > 100
        assert "FULL DOCUMENT MODE" in FULL_DOCUMENT_ASSEMBLY_PROMPT

    def test_build_full_document_prompt(self) -> None:
        """Test building the full document prompt with clauses."""
        clauses = [
            {
                "metadata": {
                    "pasal_number": "Pasal 1",
                    "section_name": "DEFINISI",
                },
                "document": "Isi: Istilah dalam kontrak [Nama Perusahaan]\nVariabel: Nama Perusahaan",
            },
            {
                "metadata": {
                    "pasal_number": "Pasal 2",
                    "section_name": "LINGKUP PEKERJAAN",
                },
                "document": "Isi: Penyedia wajib melaksanakan pekerjaan\nVariabel: ",
            },
        ]
        variables = {"Nama Perusahaan": "PT PLN (Persero)"}

        prompt = build_full_document_prompt(clauses=clauses, variables=variables)
        assert "Pasal 1" in prompt
        assert "Pasal 2" in prompt
        assert "DEFINISI" in prompt
        assert "LINGKUP PEKERJAAN" in prompt
        assert "PT PLN (Persero)" in prompt
        assert "FULL DOCUMENT MODE" in prompt

    def test_build_full_document_prompt_empty_clauses(self) -> None:
        """Test building prompt with empty clause list."""
        prompt = build_full_document_prompt(clauses=[], variables={})
        assert "FULL DOCUMENT MODE" in prompt

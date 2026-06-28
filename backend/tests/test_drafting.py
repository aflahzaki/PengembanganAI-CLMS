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
    highlight_unfilled_variables,
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


class TestHighlightUnfilledVariables:
    """Test suite for highlight_unfilled_variables function."""

    def test_highlight_basic(self) -> None:
        """Test that unfilled placeholders get wrapped with mark tag."""
        html = "<p>[Nama Pihak Kedua] di [Lokasi]</p>"
        result = highlight_unfilled_variables(html)
        assert "mark" in result
        assert "variable-highlight" in result
        assert "#FFEB3B" in result
        assert "[Nama Pihak Kedua]" in result
        assert "[Lokasi]" in result

    def test_highlight_preserves_filled_values(self) -> None:
        """Test that already-replaced values (no brackets) are not highlighted."""
        html = "<p>PT PLN (Persero) di Jakarta dan [Lokasi]</p>"
        result = highlight_unfilled_variables(html)
        # Only [Lokasi] should be wrapped
        assert result.count("<mark") == 1
        assert "[Lokasi]" in result
        assert "PT PLN (Persero)" in result
        # Parentheses in company name should NOT be highlighted
        assert "(Persero)" not in result.split("mark")[0].split("mark")[-1] or "variable-highlight" not in result.split("(Persero)")[0].split(">")[-1]

    def test_highlight_no_placeholders(self) -> None:
        """Test that text without placeholders is unchanged."""
        html = "<p>Teks biasa tanpa variabel apapun.</p>"
        result = highlight_unfilled_variables(html)
        assert result == html
        assert "mark" not in result

    def test_highlight_empty_input(self) -> None:
        """Test with empty or None input."""
        assert highlight_unfilled_variables("") == ""
        assert highlight_unfilled_variables(None) is None

    def test_highlight_multiple_placeholders(self) -> None:
        """Test with multiple placeholders in the same text."""
        html = "<p>[Nama] dari [Perusahaan] di [Alamat]</p>"
        result = highlight_unfilled_variables(html)
        assert result.count("<mark") == 3
        assert result.count("</mark>") == 3

    def test_highlight_nested_html(self) -> None:
        """Test that highlighting works within nested HTML elements."""
        html = "<div><h2>Pasal 1</h2><p>Pihak [Nama] beralamat di [Alamat]</p></div>"
        result = highlight_unfilled_variables(html)
        assert "<mark" in result
        assert "[Nama]</mark>" in result
        assert "[Alamat]</mark>" in result

    def test_highlight_does_not_match_html_attributes(self) -> None:
        """Test that bracket-like patterns in HTML attributes are not matched."""
        # Square brackets in attribute values are unlikely but test edge case
        html = '<p class="test">[Variabel Satu]</p>'
        result = highlight_unfilled_variables(html)
        assert result.count("<mark") == 1
        assert "[Variabel Satu]" in result

    def test_highlight_after_replacement(self) -> None:
        """Integration test: replace some variables, then highlight unfilled ones."""
        text = "[Nama] dari [Perusahaan] di [Alamat]"
        mapping = {"Nama": "Budi"}
        # First replace what we can
        partially_filled = replace_placeholders(text, mapping)
        # Then highlight what's left
        result = highlight_unfilled_variables(partially_filled)
        # Budi should be plain text (no highlight)
        assert "Budi" in result
        assert "Budi</mark>" not in result
        # [Perusahaan] and [Alamat] should be highlighted
        assert "[Perusahaan]</mark>" in result
        assert "[Alamat]</mark>" in result


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

    def test_full_document_prompt_includes_formatting_rules(self) -> None:
        """Test that full document prompt includes formatting instructions."""
        assert "pasal-separator" in FULL_DOCUMENT_ASSEMBLY_PROMPT
        assert "margin-bottom: 12px" in FULL_DOCUMENT_ASSEMBLY_PROMPT
        assert "line-height: 1.6" in FULL_DOCUMENT_ASSEMBLY_PROMPT
        assert "text-align: justify" in FULL_DOCUMENT_ASSEMBLY_PROMPT
        assert 'type="1"' in FULL_DOCUMENT_ASSEMBLY_PROMPT
        assert 'type="a"' in FULL_DOCUMENT_ASSEMBLY_PROMPT

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


class TestDirectVariableFillFormatting:
    """Test suite for _direct_variable_fill formatting output."""

    def _create_service(self):
        """Create a DraftingService instance without dependencies."""
        from app.services.drafting_service import DraftingService

        service = DraftingService.__new__(DraftingService)
        return service

    def test_output_has_contract_document_wrapper(self) -> None:
        """Test that output is wrapped in contract-document div."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "DEFINISI"},
                "document": "Isi: Teks definisi.\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        assert 'class="contract-document"' in result

    def test_title_is_centered(self) -> None:
        """Test that the contract title h1 has center alignment."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "TEST"},
                "document": "Isi: Test content.\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        assert "text-align: center" in result
        assert "KONTRAK HARGA SATUAN" in result

    def test_pasal_separator_between_sections(self) -> None:
        """Test that hr separator exists between Pasal sections."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "DEFINISI"},
                "document": "Isi: Teks pasal 1.\nVariabel: ",
            },
            {
                "metadata": {"pasal_number": "Pasal 2", "section_name": "LINGKUP"},
                "document": "Isi: Teks pasal 2.\nVariabel: ",
            },
        ]
        result = service._direct_variable_fill(clauses, {})
        assert "pasal-separator" in result
        assert "<hr" in result

    def test_no_separator_before_first_section(self) -> None:
        """Test that there is no hr separator before the first Pasal."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "DEFINISI"},
                "document": "Isi: First section.\nVariabel: ",
            },
        ]
        result = service._direct_variable_fill(clauses, {})
        # The hr should NOT appear before the first section
        h1_pos = result.find("<h1")
        h2_pos = result.find("<h2")
        hr_pos = result.find("<hr")
        if hr_pos != -1:
            # If there's an hr, it should be after the first h2
            assert hr_pos > h2_pos

    def test_paragraphs_have_margin_and_justify(self) -> None:
        """Test that paragraphs have proper margin and text-align styles."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "TEST"},
                "document": "Isi: Paragraf pertama kontrak ini.\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        assert "margin-bottom: 12px" in result
        assert "line-height: 1.6" in result
        assert "text-align: justify" in result

    def test_main_numbered_list_uses_ol_type_1(self) -> None:
        """Test that main numbered items use <ol type='1'>."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "DEFINISI"},
                "document": "Isi: Ketentuan berikut:\n1. Item pertama\n2. Item kedua\n3. Item ketiga\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        assert '<ol type="1"' in result
        assert "<li" in result
        assert "Item pertama" in result
        assert "Item kedua" in result
        assert "Item ketiga" in result

    def test_sub_letter_list_uses_ol_type_a(self) -> None:
        """Test that sub-letter items use <ol type='a'> with margin-left."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "DEFINISI"},
                "document": "Isi: Ketentuan:\n1. Item utama\na. Sub item A\nb. Sub item B\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        assert '<ol type="a"' in result
        assert "margin-left" in result
        assert "Sub item A" in result
        assert "Sub item B" in result

    def test_deep_sub_items_with_parenthesis(self) -> None:
        """Test that deep sub-items (1) 2) 3)) are handled."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "TEST"},
                "document": "Isi: Ketentuan:\n1. Item utama\na. Sub item\n1) Deep item satu\n2) Deep item dua\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        assert "Deep item satu" in result
        assert "Deep item dua" in result
        # Should have nested ol elements
        assert result.count("<ol") >= 3  # main + sub + deep

    def test_heading_has_proper_styling(self) -> None:
        """Test that h2 headings have proper font and margin styles."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "DEFINISI"},
                "document": "Isi: Content.\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        assert "font-size: 14px" in result
        assert "font-weight: bold" in result
        assert "margin-top: 24px" in result
        assert "margin-bottom: 12px" in result

    def test_variable_replacement_in_formatted_output(self) -> None:
        """Test that variables are correctly replaced in the formatted output."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "IDENTITAS"},
                "document": "Isi: [Nama Pihak Pertama] dari [Perusahaan].\nVariabel: Nama Pihak Pertama, Perusahaan",
            }
        ]
        variables = {"Nama Pihak Pertama": "Ir. Budi Santoso"}
        result = service._direct_variable_fill(clauses, variables)
        assert "Ir. Budi Santoso" in result
        assert "[Perusahaan]" in result  # unfilled stays as placeholder

    def test_mixed_content_paragraphs_and_lists(self) -> None:
        """Test that mixed content (paragraphs + lists) is formatted correctly."""
        service = self._create_service()
        clauses = [
            {
                "metadata": {"pasal_number": "Pasal 1", "section_name": "UMUM"},
                "document": "Isi: Paragraf pembuka kontrak ini.\n1. Item satu\n2. Item dua\nParagraf penutup bagian ini.\nVariabel: ",
            }
        ]
        result = service._direct_variable_fill(clauses, {})
        # Should have both <p> and <ol> elements
        assert "<p" in result
        assert "<ol" in result
        assert "Paragraf pembuka" in result
        assert "Item satu" in result
        assert "Paragraf penutup" in result

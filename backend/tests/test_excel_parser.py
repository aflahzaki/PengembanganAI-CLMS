"""Tests for the Excel parser module.

Tests parsing of the KHS Material Ketenagalistrikan sheet
and extraction of clause data.
"""

import sys
from pathlib import Path

import pytest

# Ensure backend is in path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.utils.excel_parser import ClauseData, ExcelParser


class TestExcelParser:
    """Test suite for ExcelParser class."""

    @pytest.fixture
    def parser(self) -> ExcelParser:
        """Create an ExcelParser instance pointing to test data."""
        templates_dir = backend_dir / "data" / "templates"
        return ExcelParser(templates_dir=str(templates_dir))

    def test_parser_initialization(self, parser: ExcelParser) -> None:
        """Test that parser initializes correctly."""
        assert parser is not None
        assert "ExcelParser" in repr(parser)

    def test_get_template_path(self, parser: ExcelParser) -> None:
        """Test that template path is resolved correctly."""
        path = parser.get_template_path()
        assert path.exists()
        assert path.name == "CLMS Pemetaan Kontrak.xlsx"

    def test_parse_khs_material_sheet(self, parser: ExcelParser) -> None:
        """Test parsing of KHS Material Ketenagalistrikan sheet."""
        clauses = parser.parse_khs_material_sheet()

        # Should extract multiple clauses
        assert len(clauses) > 0
        # Based on the briefing, approximately 45 Pasals
        assert len(clauses) >= 20, f"Expected at least 20 clauses, got {len(clauses)}"

        # First clause should have data
        first = clauses[0]
        assert isinstance(first, ClauseData)
        assert first.pasal_number != ""
        assert first.template_name == "KHS Material Ketenagalistrikan"

    def test_clause_data_structure(self, parser: ExcelParser) -> None:
        """Test that parsed clauses have the expected structure."""
        clauses = parser.parse_khs_material_sheet()

        for clause in clauses:
            assert hasattr(clause, "pasal_number")
            assert hasattr(clause, "section_name")
            assert hasattr(clause, "clause_text")
            assert hasattr(clause, "variables")
            assert hasattr(clause, "is_mandatory")
            assert isinstance(clause.variables, list)

    def test_clause_to_dict(self, parser: ExcelParser) -> None:
        """Test conversion of ClauseData to dictionary."""
        clauses = parser.parse_khs_material_sheet()
        first = clauses[0]

        d = first.to_dict()
        assert "pasal_number" in d
        assert "section_name" in d
        assert "clause_text" in d
        assert "variables" in d
        assert "is_mandatory" in d
        assert "template_name" in d

    def test_variables_extraction(self, parser: ExcelParser) -> None:
        """Test that variables are extracted from clauses."""
        clauses = parser.parse_khs_material_sheet()

        # At least some clauses should have variables
        clauses_with_vars = [c for c in clauses if c.variables]
        assert len(clauses_with_vars) > 0, "Expected some clauses to have variables"

    def test_parse_pemetaan_kontrak_sheet(self, parser: ExcelParser) -> None:
        """Test parsing of Pemetaan Kontrak sheet."""
        status_mapping = parser.parse_pemetaan_kontrak_sheet()

        # Should return a dictionary
        assert isinstance(status_mapping, dict)
        # May be empty if the sheet structure doesn't match exactly,
        # but should not raise an error
        # The function should handle the sheet gracefully

    def test_parse_all(self, parser: ExcelParser) -> None:
        """Test comprehensive parsing of all sheets."""
        data = parser.parse_all()

        assert "template_name" in data
        assert "clauses" in data
        assert "status_mapping" in data
        assert "total_clauses" in data
        assert "total_variables" in data

        assert data["template_name"] == "KHS Material Ketenagalistrikan"
        assert data["total_clauses"] > 0


class TestClauseData:
    """Test suite for ClauseData class."""

    def test_creation(self) -> None:
        """Test ClauseData creation."""
        clause = ClauseData(
            pasal_number="Pasal 1",
            section_name="DEFINISI",
            clause_text="Dalam kontrak ini [Nama] berarti...",
            variables=["Nama", "Alamat"],
            is_mandatory=True,
        )

        assert clause.pasal_number == "Pasal 1"
        assert clause.section_name == "DEFINISI"
        assert len(clause.variables) == 2
        assert clause.is_mandatory is True

    def test_repr(self) -> None:
        """Test string representation."""
        clause = ClauseData(
            pasal_number="Pasal 1",
            section_name="TEST",
            clause_text="text",
            variables=["a", "b"],
        )
        repr_str = repr(clause)
        assert "Pasal 1" in repr_str
        assert "TEST" in repr_str

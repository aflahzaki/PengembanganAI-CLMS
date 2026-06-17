"""Tests for the RAG pipeline (ingest and retrieval).

Tests ingestion of clauses into a temporary ChromaDB instance
and retrieval operations.
"""

import sys
import tempfile
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.rag.ingest import IngestService
from app.rag.retriever import RetrieverService
from app.utils.excel_parser import ClauseData


class TestIngestService:
    """Test suite for IngestService."""

    @pytest.fixture
    def temp_db(self, tmp_path: Path) -> str:
        """Create a temporary directory for ChromaDB."""
        return str(tmp_path / "test_chroma_db")

    @pytest.fixture
    def sample_clauses(self) -> list:
        """Create sample clause data for testing."""
        return [
            ClauseData(
                pasal_number="Pasal 1",
                section_name="DEFINISI DAN INTERPRETASI",
                clause_text="Dalam Kontrak ini istilah berikut memiliki arti: [Nama Pengadaan] adalah pengadaan yang dilaksanakan oleh [Nama Perusahaan].",
                variables=["Nama Pengadaan", "Nama Perusahaan"],
                is_mandatory=True,
            ),
            ClauseData(
                pasal_number="Pasal 2",
                section_name="HIERARKI DOKUMEN",
                clause_text="Dokumen-dokumen berikut merupakan satu kesatuan dari Kontrak ini.",
                variables=[],
                is_mandatory=True,
            ),
            ClauseData(
                pasal_number="Pasal 3",
                section_name="LINGKUP PEKERJAAN",
                clause_text="Penyedia wajib melaksanakan pekerjaan [Uraian Pekerjaan] sesuai spesifikasi.",
                variables=["Uraian Pekerjaan"],
                is_mandatory=True,
            ),
            ClauseData(
                pasal_number="Pasal 4",
                section_name="HARGA SATUAN",
                clause_text="Harga satuan sebesar [Nilai Kontrak] sudah termasuk pajak.",
                variables=["Nilai Kontrak"],
                is_mandatory=False,
            ),
        ]

    def test_ingest_clauses(self, temp_db: str, sample_clauses: list) -> None:
        """Test basic clause ingestion."""
        service = IngestService(
            persist_directory=temp_db,
            collection_name="test_clauses",
        )

        result = service.ingest_clauses(sample_clauses)

        assert result["total_ingested"] == 4
        assert result["collection_count"] == 4

    def test_ingest_stats(self, temp_db: str, sample_clauses: list) -> None:
        """Test collection statistics after ingestion."""
        service = IngestService(
            persist_directory=temp_db,
            collection_name="test_stats",
        )

        service.ingest_clauses(sample_clauses)
        stats = service.get_stats()

        assert stats["document_count"] == 4
        assert stats["collection_name"] == "test_stats"

    def test_reingest_replaces_existing(self, temp_db: str, sample_clauses: list) -> None:
        """Test that re-ingestion replaces existing documents."""
        service = IngestService(
            persist_directory=temp_db,
            collection_name="test_reingest",
        )

        # First ingest
        service.ingest_clauses(sample_clauses)
        assert service.get_stats()["document_count"] == 4

        # Second ingest should replace, not duplicate
        service.ingest_clauses(sample_clauses)
        assert service.get_stats()["document_count"] == 4


class TestRetrieverService:
    """Test suite for RetrieverService."""

    @pytest.fixture
    def populated_db(self, tmp_path: Path) -> str:
        """Create and populate a temporary ChromaDB."""
        db_path = str(tmp_path / "test_retriever_db")

        clauses = [
            ClauseData(
                pasal_number="Pasal 1",
                section_name="DEFINISI DAN INTERPRETASI",
                clause_text="Definisi istilah dalam kontrak pengadaan material.",
                variables=["Nama Pengadaan"],
                is_mandatory=True,
            ),
            ClauseData(
                pasal_number="Pasal 2",
                section_name="LINGKUP PEKERJAAN",
                clause_text="Lingkup pekerjaan mencakup pengadaan material ketenagalistrikan.",
                variables=["Uraian Pekerjaan"],
                is_mandatory=True,
            ),
            ClauseData(
                pasal_number="Pasal 3",
                section_name="HARGA DAN PEMBAYARAN",
                clause_text="Harga kontrak dan ketentuan pembayaran.",
                variables=["Nilai Kontrak", "Nomor Rekening"],
                is_mandatory=False,
            ),
        ]

        ingest = IngestService(
            persist_directory=db_path,
            collection_name="test_retriever",
        )
        ingest.ingest_clauses(clauses, template_name="Test Template")

        return db_path

    def test_query_by_topic(self, populated_db: str) -> None:
        """Test semantic search by topic."""
        retriever = RetrieverService(
            persist_directory=populated_db,
            collection_name="test_retriever",
        )

        results = retriever.query_by_topic("definisi dan interpretasi")
        assert len(results["documents"]) > 0

    def test_get_all_clauses(self, populated_db: str) -> None:
        """Test retrieving all clauses for a template."""
        retriever = RetrieverService(
            persist_directory=populated_db,
            collection_name="test_retriever",
        )

        clauses = retriever.get_all_clauses_for_template("Test Template")
        assert len(clauses) == 3

        # Verify ordering
        for i, clause in enumerate(clauses):
            assert clause["metadata"]["order_index"] == i

    def test_get_mandatory_clauses(self, populated_db: str) -> None:
        """Test retrieving only mandatory clauses."""
        retriever = RetrieverService(
            persist_directory=populated_db,
            collection_name="test_retriever",
        )

        mandatory = retriever.get_mandatory_clauses("Test Template")
        assert len(mandatory) == 2

        for clause in mandatory:
            assert clause["metadata"]["is_mandatory"] is True

    def test_get_clause_by_pasal(self, populated_db: str) -> None:
        """Test retrieving a specific clause by Pasal number."""
        retriever = RetrieverService(
            persist_directory=populated_db,
            collection_name="test_retriever",
        )

        clause = retriever.get_clause_by_pasal("Pasal 1")
        assert clause is not None
        assert clause["metadata"]["pasal_number"] == "Pasal 1"

    def test_collection_stats(self, populated_db: str) -> None:
        """Test collection statistics."""
        retriever = RetrieverService(
            persist_directory=populated_db,
            collection_name="test_retriever",
        )

        stats = retriever.get_collection_stats()
        assert stats["total_documents"] == 3

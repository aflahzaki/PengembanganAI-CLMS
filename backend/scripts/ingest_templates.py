"""CLI script to ingest contract templates from Excel into ChromaDB.

Loads the Excel template file, parses all sheets using ExcelParser,
and stores the extracted clauses in ChromaDB for RAG retrieval.

Usage:
    cd backend
    python scripts/ingest_templates.py
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.rag.ingest import IngestService
from app.utils.excel_parser import ExcelParser


def main() -> None:
    """Main function to run the template ingestion pipeline."""
    print("=" * 60)
    print("CLMS Template Ingestion Pipeline")
    print("=" * 60)

    # Step 1: Initialize parser
    print(f"\n[1/4] Initializing parser...")
    print(f"  Templates directory: {settings.templates_absolute_path}")

    parser = ExcelParser()

    # Step 2: Parse Excel file
    print(f"\n[2/4] Parsing Excel template...")
    try:
        template_path = parser.get_template_path()
        print(f"  Found template: {template_path.name}")
    except FileNotFoundError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    # Parse all data
    data = parser.parse_all(template_path)
    clauses = data["clauses"]

    print(f"  Template: {data['template_name']}")
    print(f"  Total clauses extracted: {data['total_clauses']}")
    print(f"  Total variables found: {data['total_variables']}")

    # Step 3: Display parsed clauses summary
    print(f"\n[3/4] Clause summary:")
    for i, clause in enumerate(clauses[:10]):
        vars_str = f" [{len(clause.variables)} vars]" if clause.variables else ""
        print(f"  {i+1:3d}. {clause.pasal_number}: {clause.section_name}{vars_str}")
    if len(clauses) > 10:
        print(f"  ... and {len(clauses) - 10} more clauses")

    # Step 4: Ingest into ChromaDB
    print(f"\n[4/4] Ingesting into ChromaDB...")
    print(f"  Database path: {settings.chroma_db_absolute_path}")

    ingest_service = IngestService(
        persist_directory=str(settings.chroma_db_absolute_path)
    )

    result = ingest_service.ingest_clauses(
        clauses=clauses,
        template_name=data["template_name"],
    )

    print(f"  Documents ingested: {result['total_ingested']}")
    print(f"  Collection: {result['collection_name']}")
    print(f"  Total in collection: {result['collection_count']}")

    # Verify
    stats = ingest_service.get_stats()
    print(f"\n{'=' * 60}")
    print(f"Ingestion complete!")
    print(f"  Collection '{stats['collection_name']}': {stats['document_count']} documents")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

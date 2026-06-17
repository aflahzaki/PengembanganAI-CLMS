"""Template registry for managing multiple contract templates.

Provides a registry system for adding and managing different contract
template types. Currently supports KHS Material Ketenagalistrikan,
extensible for KHS Jasa, Kontrak Lump Sum, SPK, and others.

Usage:
    from app.rag.template_registry import TemplateRegistry

    registry = TemplateRegistry()
    registry.register(
        name="KHS Material Ketenagalistrikan",
        description="Kontrak Harga Satuan untuk pengadaan material",
        source_file="CLMS Pemetaan Kontrak.xlsx",
        sheet_mapping={"clauses": "KHS Material Ketenagalistrikan", "mapping": "Pemetaan Kontrak "},
    )
    templates = registry.list_templates()
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


@dataclass
class TemplateMetadata:
    """Metadata for a registered contract template.

    Attributes:
        name: Unique template identifier/name.
        description: Human-readable description of the template.
        source_file: Excel filename containing the template data.
        sheet_mapping: Mapping of logical names to actual sheet names.
        collection_name: ChromaDB collection name for this template.
        parsing_strategy: Strategy identifier for how to parse the Excel.
        variables: List of known variable names for this template.
        is_ingested: Whether this template has been ingested into ChromaDB.
    """

    name: str
    description: str
    source_file: str
    sheet_mapping: Dict[str, str]
    collection_name: str = "contract_clauses"
    parsing_strategy: str = "khs_material"
    variables: List[str] = field(default_factory=list)
    is_ingested: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "source_file": self.source_file,
            "sheet_mapping": self.sheet_mapping,
            "collection_name": self.collection_name,
            "parsing_strategy": self.parsing_strategy,
            "variables": self.variables,
            "is_ingested": self.is_ingested,
        }


class TemplateRegistry:
    """Registry for managing multiple contract templates.

    Extensible design:
    1. Register new template type
    2. Provide Excel file path
    3. Specify sheet names and parsing strategy
    4. Run ingestion to store in ChromaDB collection

    Each template gets its own ChromaDB collection for isolation,
    or can share a collection with template_name metadata filtering.

    Supported parsing strategies:
    - "khs_material": Parse KHS Material format (Pasal/Section/Text/Variables)
    - "khs_jasa": Parse KHS Jasa format (future)
    - "lump_sum": Parse Kontrak Lump Sum format (future)
    - "spk": Parse SPK format (future)
    """

    def __init__(self):
        """Initialize the template registry with default templates."""
        self._templates: Dict[str, TemplateMetadata] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the default KHS Material template."""
        self.register(
            name="KHS Material Ketenagalistrikan",
            description=(
                "Kontrak Harga Satuan untuk pengadaan material "
                "ketenagalistrikan PLN. Berisi 45 pasal standar "
                "dengan variabel yang dapat diisi sesuai kebutuhan kontrak."
            ),
            source_file="CLMS Pemetaan Kontrak.xlsx",
            sheet_mapping={
                "clauses": "KHS Material Ketenagalistrikan",
                "mapping": "Pemetaan Kontrak ",
            },
            collection_name="contract_clauses",
            parsing_strategy="khs_material",
        )

    def register(
        self,
        name: str,
        description: str,
        source_file: str,
        sheet_mapping: Dict[str, str],
        collection_name: Optional[str] = None,
        parsing_strategy: str = "khs_material",
    ) -> TemplateMetadata:
        """Register a new template in the registry.

        Args:
            name: Unique template name/identifier.
            description: Human-readable template description.
            source_file: Excel filename (relative to templates directory).
            sheet_mapping: Dict mapping logical names to sheet names.
                          Expected keys: "clauses", "mapping" (optional).
            collection_name: ChromaDB collection name. Defaults to
                           sanitized template name.
            parsing_strategy: How to parse the Excel file.

        Returns:
            TemplateMetadata for the registered template.

        Raises:
            ValueError: If a template with the same name already exists
                       and overwrite is not intended.
        """
        if collection_name is None:
            # Generate collection name from template name
            collection_name = name.lower().replace(" ", "_").replace("-", "_")
            # ChromaDB collection names must be 3-63 chars, alphanumeric + underscore
            collection_name = "".join(
                c for c in collection_name if c.isalnum() or c == "_"
            )[:63]

        metadata = TemplateMetadata(
            name=name,
            description=description,
            source_file=source_file,
            sheet_mapping=sheet_mapping,
            collection_name=collection_name,
            parsing_strategy=parsing_strategy,
        )

        self._templates[name] = metadata
        return metadata

    def get_template(self, name: str) -> Optional[TemplateMetadata]:
        """Get template metadata by name.

        Args:
            name: Template name to look up.

        Returns:
            TemplateMetadata if found, None otherwise.
        """
        return self._templates.get(name)

    def list_templates(self) -> List[TemplateMetadata]:
        """List all registered templates.

        Returns:
            List of all TemplateMetadata objects in the registry.
        """
        return list(self._templates.values())

    def ingest_template(
        self,
        name: str,
        persist_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest a registered template into ChromaDB.

        Parses the source Excel file according to the template's
        parsing strategy and stores the clauses in ChromaDB.

        Args:
            name: Template name to ingest.
            persist_directory: Optional ChromaDB persistence path.

        Returns:
            Dict with ingestion statistics.

        Raises:
            ValueError: If template name is not registered.
            FileNotFoundError: If source file does not exist.
        """
        template = self.get_template(name)
        if template is None:
            raise ValueError(f"Template '{name}' is not registered")

        # Import here to avoid circular imports
        from app.rag.ingest import IngestService
        from app.utils.excel_parser import ExcelParser

        # Resolve source file path
        templates_dir = settings.templates_absolute_path
        source_path = templates_dir / template.source_file

        if not source_path.exists():
            raise FileNotFoundError(
                f"Source file not found: {source_path}"
            )

        # Parse based on strategy
        parser = ExcelParser(templates_dir=str(templates_dir))
        clauses = self._parse_with_strategy(
            parser, source_path, template
        )

        # Ingest into ChromaDB
        db_path = persist_directory or str(settings.chroma_db_absolute_path)
        ingest_service = IngestService(
            persist_directory=db_path,
            collection_name=template.collection_name,
        )

        result = ingest_service.ingest_clauses(
            clauses=clauses,
            template_name=template.name,
        )

        # Update registry state
        template.is_ingested = True
        template.variables = list(
            set(var for clause in clauses for var in clause.variables)
        )

        return result

    def _parse_with_strategy(
        self,
        parser,
        source_path: Path,
        template: TemplateMetadata,
    ) -> list:
        """Parse an Excel file using the specified strategy.

        Args:
            parser: ExcelParser instance.
            source_path: Path to the Excel file.
            template: Template metadata with parsing strategy info.

        Returns:
            List of ClauseData objects.
        """
        strategy = template.parsing_strategy

        if strategy == "khs_material":
            data = parser.parse_all(source_path)
            return data["clauses"]
        else:
            # Future strategies can be added here
            # For now, fall back to the KHS material parser
            data = parser.parse_all(source_path)
            return data["clauses"]

    def unregister(self, name: str) -> bool:
        """Remove a template from the registry.

        Args:
            name: Template name to remove.

        Returns:
            True if removed, False if not found.
        """
        if name in self._templates:
            del self._templates[name]
            return True
        return False

    def is_registered(self, name: str) -> bool:
        """Check if a template is registered.

        Args:
            name: Template name to check.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._templates

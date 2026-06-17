"""Template API routes for querying available templates.

Provides endpoints for listing templates and retrieving template details.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_retriever_service
from app.models.schemas import ClauseSchema, TemplateInfo, VariableSchema
from app.rag.retriever import RetrieverService

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=List[TemplateInfo])
async def list_templates(
    retriever: RetrieverService = Depends(get_retriever_service),
) -> List[TemplateInfo]:
    """List all available contract templates.

    Returns:
        List of TemplateInfo with template names and metadata.
    """
    # Currently we have one template - KHS Material Ketenagalistrikan
    templates = []

    clauses = retriever.get_all_clauses_for_template(
        "KHS Material Ketenagalistrikan"
    )

    if clauses:
        # Extract all variables from clauses
        all_variables = set()
        mandatory_count = 0
        optional_count = 0

        for clause in clauses:
            meta = clause.get("metadata", {})
            vars_list = meta.get("variables_list", "")
            if vars_list:
                for v in vars_list.split(", "):
                    v = v.strip()
                    if v:
                        all_variables.add(v)

            if meta.get("is_mandatory", True):
                mandatory_count += 1
            else:
                optional_count += 1

        variable_schemas = [
            VariableSchema(name=v, required=True)
            for v in sorted(all_variables)
        ]

        templates.append(
            TemplateInfo(
                name="KHS Material Ketenagalistrikan",
                description="Kontrak Harga Satuan untuk pengadaan material ketenagalistrikan PLN",
                clauses_count=len(clauses),
                variables=variable_schemas,
                mandatory_clauses=mandatory_count,
                optional_clauses=optional_count,
            )
        )

    return templates


@router.get("/{name}", response_model=TemplateInfo)
async def get_template(
    name: str,
    retriever: RetrieverService = Depends(get_retriever_service),
) -> TemplateInfo:
    """Get details for a specific template.

    Args:
        name: Template name to look up.

    Returns:
        TemplateInfo with full template details.

    Raises:
        HTTPException: If template is not found.
    """
    clauses = retriever.get_all_clauses_for_template(name)

    if not clauses:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{name}' not found",
        )

    all_variables = set()
    mandatory_count = 0
    optional_count = 0

    for clause in clauses:
        meta = clause.get("metadata", {})
        vars_list = meta.get("variables_list", "")
        if vars_list:
            for v in vars_list.split(", "):
                v = v.strip()
                if v:
                    all_variables.add(v)

        if meta.get("is_mandatory", True):
            mandatory_count += 1
        else:
            optional_count += 1

    variable_schemas = [
        VariableSchema(name=v, required=True)
        for v in sorted(all_variables)
    ]

    return TemplateInfo(
        name=name,
        description="Kontrak Harga Satuan untuk pengadaan material ketenagalistrikan PLN",
        clauses_count=len(clauses),
        variables=variable_schemas,
        mandatory_clauses=mandatory_count,
        optional_clauses=optional_count,
    )

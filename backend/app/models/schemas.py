"""Pydantic models for request/response schemas.

Defines all data transfer objects used across the API endpoints.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class VariableSchema(BaseModel):
    """Schema for a template variable."""

    name: str = Field(..., description="Variable name as it appears in the template")
    description: Optional[str] = Field(None, description="Description of what this variable represents")
    required: bool = Field(True, description="Whether this variable must be filled")
    default_value: Optional[str] = Field(None, description="Default value if not provided")


class ClauseSchema(BaseModel):
    """Schema for a contract clause."""

    pasal_number: str = Field(..., description="Pasal/article identifier")
    section_name: str = Field(..., description="Name of the clause section")
    clause_text: str = Field(..., description="Full text of the clause")
    variables: List[str] = Field(default_factory=list, description="List of placeholder variables")
    is_mandatory: bool = Field(True, description="Whether this clause is mandatory")


class TemplateInfo(BaseModel):
    """Schema for template information response."""

    name: str = Field(..., description="Template name")
    description: str = Field("", description="Template description")
    clauses_count: int = Field(0, description="Number of clauses in the template")
    variables: List[VariableSchema] = Field(
        default_factory=list, description="All variables across all clauses"
    )
    mandatory_clauses: int = Field(0, description="Number of mandatory clauses")
    optional_clauses: int = Field(0, description="Number of optional clauses")


class DraftRequest(BaseModel):
    """Request schema for contract draft generation."""

    template_name: str = Field(
        "KHS Material Ketenagalistrikan",
        description="Name of the contract template to use",
    )
    variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of variable names to their values",
    )
    include_optional: bool = Field(
        True, description="Whether to include optional clauses"
    )


class DraftResponse(BaseModel):
    """Response schema for generated contract draft."""

    html_content: str = Field(..., description="Generated contract in HTML format")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about the generation (clauses used, variables filled, etc.)",
    )
    unfilled_variables: List[str] = Field(
        default_factory=list,
        description="List of variables that could not be filled",
    )


class ExportRequest(BaseModel):
    """Request schema for document export."""

    html_content: str = Field(..., description="HTML content to export")
    format: Literal["docx"] = Field("docx", description="Export format (only docx supported)")
    filename: Optional[str] = Field(None, description="Optional output filename")


class ExportResponse(BaseModel):
    """Response schema for document export."""

    filename: str = Field(..., description="Generated filename")
    format: str = Field(..., description="Export format used")
    size_bytes: int = Field(0, description="File size in bytes")


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field("ok", description="Service status")
    version: str = Field(..., description="Application version")
    chroma_db_status: str = Field(..., description="ChromaDB connection status")
    templates_loaded: int = Field(0, description="Number of templates loaded")

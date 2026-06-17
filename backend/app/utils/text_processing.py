"""Text processing utilities for legal document handling.

Provides functions for extracting and replacing placeholders,
formatting clauses for embedding, and cleaning legal text.
"""

import re
from typing import Dict, List, Optional


def extract_placeholders(text: str) -> List[str]:
    """Extract all [PLACEHOLDER] patterns from text.

    Args:
        text: Input text containing [Variable Name] patterns.

    Returns:
        List of unique placeholder names (without brackets).

    Example:
        >>> extract_placeholders("Kontrak [Nomor Kontrak] tanggal [Tanggal]")
        ['Nomor Kontrak', 'Tanggal']
    """
    if not text:
        return []
    pattern = r"\[([^\[\]]+)\]"
    matches = re.findall(pattern, text)
    # Return unique placeholders preserving order
    seen = set()
    unique = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            unique.append(match)
    return unique


def replace_placeholders(text: str, mapping: Dict[str, str]) -> str:
    """Replace [PLACEHOLDER] patterns with actual values.

    Args:
        text: Input text containing placeholders.
        mapping: Dictionary mapping placeholder names to their values.

    Returns:
        Text with placeholders replaced by their mapped values.
        Unmapped placeholders remain unchanged.

    Example:
        >>> replace_placeholders("[Nama] Corp", {"Nama": "PT ABC"})
        'PT ABC Corp'
    """
    if not text or not mapping:
        return text

    def replacer(match: re.Match) -> str:
        placeholder_name = match.group(1)
        return mapping.get(placeholder_name, match.group(0))

    pattern = r"\[([^\[\]]+)\]"
    return re.sub(pattern, replacer, text)


def format_clause_for_embedding(
    pasal_number: str,
    section_name: str,
    clause_text: str,
    variables: Optional[List[str]] = None,
) -> str:
    """Format a clause for embedding in the vector store.

    Creates a structured text representation optimized for semantic search.

    Args:
        pasal_number: The article/pasal number identifier.
        section_name: Name of the section/clause.
        clause_text: Full text of the clause.
        variables: Optional list of variable names used in the clause.

    Returns:
        Formatted string suitable for embedding.
    """
    parts = []

    if pasal_number:
        parts.append(f"Pasal: {pasal_number}")
    if section_name:
        parts.append(f"Judul: {section_name}")
    if clause_text:
        parts.append(f"Isi: {clause_text}")
    if variables:
        parts.append(f"Variabel: {', '.join(variables)}")

    return "\n".join(parts)


def clean_legal_text(text: str) -> str:
    """Clean legal text by normalizing whitespace and formatting.

    Removes excessive whitespace, normalizes line breaks,
    and trims leading/trailing spaces while preserving paragraph structure.

    Args:
        text: Raw legal text to clean.

    Returns:
        Cleaned text with normalized formatting.
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive blank lines (keep max 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalize spaces (but preserve newlines)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Remove leading/trailing whitespace from each line
        cleaned = line.strip()
        # Normalize multiple spaces to single space
        cleaned = re.sub(r"  +", " ", cleaned)
        cleaned_lines.append(cleaned)

    text = "\n".join(cleaned_lines)

    # Remove leading/trailing whitespace from entire text
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """Split legal text into sentences.

    Handles Indonesian legal text patterns including numbered items
    and common legal abbreviations.

    Args:
        text: Legal text to split into sentences.

    Returns:
        List of sentences.
    """
    if not text:
        return []

    # Split on period followed by space and uppercase, or newline
    # But preserve numbering patterns like "1." or "a."
    sentences = re.split(r"(?<=[.;])\s+(?=[A-Z(])", text)
    return [s.strip() for s in sentences if s.strip()]

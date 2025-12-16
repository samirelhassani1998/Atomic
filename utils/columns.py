"""
Column normalization utilities for handling case-insensitive
and variant column name mappings.
"""

import re
from typing import Dict, List, Tuple
import pandas as pd


# Canonical column names (target format)
CANONICAL_COLUMNS = {
    "indicateur_principal": "Indicateur_principal",
    "indicateur": "indicateur",
}

# Additional known aliases (lowercase -> canonical)
COLUMN_ALIASES = {
    "indicateur_principal": "Indicateur_principal",
    "indicateurprincipal": "Indicateur_principal",
    "indicateur-principal": "Indicateur_principal",
    "indicateur principal": "Indicateur_principal",
}


def clean_column_name(name: str) -> str:
    """
    Clean a column name by trimming whitespace and normalizing
    separators (replace spaces and hyphens with underscores).
    
    Args:
        name: Original column name
        
    Returns:
        Cleaned column name
    """
    # Trim whitespace
    cleaned = name.strip()
    # Replace spaces and hyphens with underscores
    cleaned = re.sub(r'[\s\-]+', '_', cleaned)
    return cleaned


def normalize_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Normalize DataFrame column names to canonical format.
    
    Performs case-insensitive matching for required columns
    and cleans up separators in all column names.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (normalized DataFrame, mapping dict of original->new names)
    """
    rename_mapping = {}
    columns_applied = {}
    
    # First pass: clean all column names
    for col in df.columns:
        cleaned = clean_column_name(col)
        if cleaned != col:
            rename_mapping[col] = cleaned
    
    # Apply initial cleaning
    if rename_mapping:
        df = df.rename(columns=rename_mapping)
        columns_applied.update(rename_mapping)
        rename_mapping = {}
    
    # Second pass: case-insensitive matching for canonical columns
    cols_lower = {col.lower(): col for col in df.columns}
    
    for canonical_lower, canonical_name in CANONICAL_COLUMNS.items():
        # Skip if canonical name already exists
        if canonical_name in df.columns:
            continue
        
        # Check for case-insensitive match
        if canonical_lower in cols_lower:
            original_col = cols_lower[canonical_lower]
            if original_col != canonical_name:
                rename_mapping[original_col] = canonical_name
    
    # Also check aliases
    for alias_lower, canonical_name in COLUMN_ALIASES.items():
        if canonical_name in df.columns:
            continue
        if alias_lower in cols_lower:
            original_col = cols_lower[alias_lower]
            if original_col != canonical_name and original_col not in rename_mapping:
                rename_mapping[original_col] = canonical_name
    
    # Apply canonical renaming
    if rename_mapping:
        df = df.rename(columns=rename_mapping)
        columns_applied.update(rename_mapping)
    
    return df, columns_applied


def get_missing_required_columns(df: pd.DataFrame, required: List[str]) -> List[str]:
    """
    Check for missing required columns (case-insensitive).
    
    Args:
        df: DataFrame to check
        required: List of required column names
        
    Returns:
        List of missing column names
    """
    df_cols_lower = {col.lower() for col in df.columns}
    missing = []
    
    for req in required:
        if req not in df.columns:
            # Also check case-insensitive
            if req.lower() not in df_cols_lower:
                missing.append(req)
    
    return missing


def format_column_mapping_message(mapping: Dict[str, str]) -> str:
    """
    Format a human-readable message about column remapping.
    
    Args:
        mapping: Dict of original -> new column names
        
    Returns:
        Formatted message string
    """
    if not mapping:
        return ""
    
    lines = [f"`{orig}` → `{new}`" for orig, new in mapping.items()]
    return "**Colonnes auto-mappées :** " + ", ".join(lines)

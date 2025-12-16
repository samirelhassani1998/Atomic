"""
Core normalization logic for transforming aggregated data
into a tidy, normalized format.
"""

import re
import unicodedata
import pandas as pd
from typing import Optional, Tuple

from utils.mappings import (
    EVENT_TYPE_MAPPING,
    RESPONSE_CODE_MAPPING,
    VALID_UNIVERSES,
    EVENT_TYPES,
    RESPONSE_CODES,
    QUALITY_OK,
    QUALITY_WARNING,
    QUALITY_ERROR,
)


def normalize_text(text: str) -> str:
    """Normalize text: trim, lowercase, remove accents."""
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()
    # Remove accents
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def parse_reponse_popin_suffix(indicateur_principal: str) -> Tuple[Optional[str], int]:
    """
    Extract universe context from ReponsePopin suffix.
    
    Examples:
        "ReponsePopin_LBP_LPM" -> ("LBP|LPM", 2)
        "ReponsePopin_LP_LBP_LPM" -> ("LP|LBP|LPM", 3)
        "ReponsePopin" -> (None, 0)
    """
    pattern = r"^reponsepopin(?:_(.+))?$"
    match = re.match(pattern, normalize_text(indicateur_principal))
    
    if not match:
        return None, 0
    
    suffix = match.group(1)
    if not suffix:
        return None, 0
    
    # Split suffix by underscore and filter valid universes
    parts = suffix.upper().split("_")
    valid_parts = [p for p in parts if p in VALID_UNIVERSES]
    
    if not valid_parts:
        return None, 0
    
    return "|".join(valid_parts), len(valid_parts)


def normalize_response_code(indicateur: str) -> Tuple[Optional[str], bool]:
    """
    Normalize response code from indicateur field.
    
    Returns:
        Tuple of (normalized_code, is_valid)
    """
    normalized = normalize_text(indicateur)
    
    if normalized in RESPONSE_CODE_MAPPING:
        return RESPONSE_CODE_MAPPING[normalized], True
    
    # Try to find partial match
    for key, value in RESPONSE_CODE_MAPPING.items():
        if key in normalized or normalized in key:
            return value, True
    
    return None, False


def determine_event_type(indicateur_principal: str) -> Tuple[str, bool]:
    """
    Determine event type from Indicateur_principal.
    
    Returns:
        Tuple of (event_type, is_recognized)
    """
    normalized = normalize_text(indicateur_principal)
    
    # Check for ReponsePopin pattern first
    if normalized.startswith("reponsepopin"):
        return "POPIN_RESPONSE", True
    
    # Check direct mapping
    if normalized in EVENT_TYPE_MAPPING:
        return EVENT_TYPE_MAPPING[normalized], True
    
    return "OTHER", False


def extract_initial_universe(indicateur_principal: str, indicateur: str) -> Tuple[Optional[str], bool]:
    """
    Extract initial universe from indicateur when applicable.
    
    Returns:
        Tuple of (universe, is_valid)
    """
    event_type, _ = determine_event_type(indicateur_principal)
    
    if event_type not in ("IDENTIFICATION", "POPIN_DISPLAYED"):
        return None, True
    
    # Check if indicateur is a valid universe
    indicateur_upper = str(indicateur).strip().upper() if pd.notna(indicateur) else ""
    
    if indicateur_upper in VALID_UNIVERSES:
        return indicateur_upper, True
    
    return indicateur_upper if indicateur_upper else None, False


def normalize_row(row: pd.Series, measure_col: Optional[str], date_col: Optional[str]) -> dict:
    """
    Normalize a single row of data.
    
    Returns:
        Dictionary with all normalized fields.
    """
    indicateur_principal = str(row.get("Indicateur_principal", "")) if pd.notna(row.get("Indicateur_principal")) else ""
    indicateur = str(row.get("indicateur", "")) if pd.notna(row.get("indicateur")) else ""
    
    # Determine event type
    event_type, event_recognized = determine_event_type(indicateur_principal)
    
    # Initialize result
    result = {
        "event_date": row.get(date_col) if date_col else None,
        "event_type": event_type,
        "popin_code": None,
        "response_code": None,
        "initial_universe": None,
        "universe_context": None,
        "universe_count": 0,
        "measure_count": 1,
        "source_indicateur_principal": indicateur_principal,
        "source_indicateur": indicateur,
        "quality_flag": QUALITY_OK,
        "quality_detail": "",
    }
    
    # Get measure value
    if measure_col and measure_col in row.index:
        try:
            result["measure_count"] = int(row[measure_col]) if pd.notna(row[measure_col]) else 1
        except (ValueError, TypeError):
            result["measure_count"] = 1
    
    quality_issues = []
    
    # Process based on event type
    if event_type == "POPIN_RESPONSE":
        # Extract response code
        response_code, response_valid = normalize_response_code(indicateur)
        result["response_code"] = response_code
        
        if not response_valid and indicateur:
            quality_issues.append(f"Unrecognized response_code: {indicateur}")
        
        # Extract universe context from suffix
        universe_context, universe_count = parse_reponse_popin_suffix(indicateur_principal)
        result["universe_context"] = universe_context
        result["universe_count"] = universe_count
        
        # Set popin code if detectable
        if "association" in normalize_text(indicateur_principal) or "association" in normalize_text(indicateur):
            result["popin_code"] = "ASSOCIATION_LIEN"
    
    elif event_type == "IDENTIFICATION":
        initial_universe, universe_valid = extract_initial_universe(indicateur_principal, indicateur)
        result["initial_universe"] = initial_universe
        
        if not universe_valid and initial_universe:
            quality_issues.append(f"Unknown universe: {initial_universe}")
    
    elif event_type == "POPIN_DISPLAYED":
        initial_universe, universe_valid = extract_initial_universe(indicateur_principal, indicateur)
        result["initial_universe"] = initial_universe
        
        normalized_principal = normalize_text(indicateur_principal)
        if "primo" in normalized_principal:
            result["popin_code"] = "PRIMO_IDENTIFICATION"
        
        if not universe_valid and initial_universe:
            quality_issues.append(f"Unknown universe: {initial_universe}")
    
    elif event_type == "OTHER":
        if not event_recognized:
            quality_issues.append(f"Unrecognized event type from: {indicateur_principal}")
    
    # Set quality flags
    if quality_issues:
        # Check if it's a warning or error
        has_unknown_universe = any("Unknown universe" in issue for issue in quality_issues)
        has_unrecognized = any("Unrecognized" in issue for issue in quality_issues)
        
        if has_unrecognized:
            result["quality_flag"] = QUALITY_ERROR
        elif has_unknown_universe:
            result["quality_flag"] = QUALITY_WARNING
        
        result["quality_detail"] = "; ".join(quality_issues)
    
    return result


def normalize_dataframe(
    df: pd.DataFrame,
    measure_col: Optional[str] = None,
    date_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Normalize an entire DataFrame.
    
    Args:
        df: Input DataFrame with Indicateur_principal and indicateur columns
        measure_col: Name of column containing measure/count values
        date_col: Name of column containing date/period values
    
    Returns:
        Normalized DataFrame with tidy structure
    """
    # Validate required columns
    required_cols = ["Indicateur_principal", "indicateur"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Normalize each row
    normalized_rows = []
    for _, row in df.iterrows():
        normalized_rows.append(normalize_row(row, measure_col, date_col))
    
    return pd.DataFrame(normalized_rows)


def get_quality_summary(df: pd.DataFrame) -> dict:
    """
    Generate a quality summary from normalized data.
    
    Returns:
        Dictionary with quality statistics.
    """
    total = len(df)
    ok_count = len(df[df["quality_flag"] == QUALITY_OK])
    warning_count = len(df[df["quality_flag"] == QUALITY_WARNING])
    error_count = len(df[df["quality_flag"] == QUALITY_ERROR])
    
    return {
        "total_rows": total,
        "ok_count": ok_count,
        "warning_count": warning_count,
        "error_count": error_count,
        "ok_pct": round(ok_count / total * 100, 1) if total > 0 else 0,
        "warning_pct": round(warning_count / total * 100, 1) if total > 0 else 0,
        "error_pct": round(error_count / total * 100, 1) if total > 0 else 0,
    }

"""
Star schema generation for normalized event data.
"""

import io
import zipfile
import pandas as pd
from typing import Dict

from utils.mappings import (
    EVENT_TYPES,
    RESPONSE_CODES,
    VALID_UNIVERSES,
)


def create_dim_event_type() -> pd.DataFrame:
    """Create event type dimension table."""
    data = [
        {"event_type_id": 1, "event_type_code": "IDENTIFICATION", "event_type_label": "User Identification"},
        {"event_type_id": 2, "event_type_code": "POPIN_DISPLAYED", "event_type_label": "Pop-in Displayed"},
        {"event_type_id": 3, "event_type_code": "POPIN_RESPONSE", "event_type_label": "Pop-in Response"},
        {"event_type_id": 4, "event_type_code": "LINK_CREATED", "event_type_label": "Link Created"},
        {"event_type_id": 5, "event_type_code": "LINK_VALIDATED", "event_type_label": "Link Validated"},
        {"event_type_id": 6, "event_type_code": "LINK_DELETED", "event_type_label": "Link Deleted"},
        {"event_type_id": 7, "event_type_code": "OTHER", "event_type_label": "Other Event"},
    ]
    return pd.DataFrame(data)


def create_dim_universe() -> pd.DataFrame:
    """Create universe dimension table."""
    data = [
        {"universe_id": 1, "universe_code": "LBP", "universe_label": "La Banque Postale"},
        {"universe_id": 2, "universe_code": "LP", "universe_label": "La Poste"},
        {"universe_id": 3, "universe_code": "LPM", "universe_label": "La Poste Mobile"},
    ]
    return pd.DataFrame(data)


def create_dim_response() -> pd.DataFrame:
    """Create response code dimension table."""
    data = [
        {"response_id": 1, "response_code": "ASSOCIATION", "response_label": "Association acceptée"},
        {"response_id": 2, "response_code": "PEUT_ETRE", "response_label": "Peut-être plus tard"},
        {"response_id": 3, "response_code": "REFUS", "response_label": "Refus"},
        {"response_id": 4, "response_code": "CLOSE", "response_label": "Fermeture sans réponse"},
    ]
    return pd.DataFrame(data)


def create_dim_popin() -> pd.DataFrame:
    """Create pop-in type dimension table."""
    data = [
        {"popin_id": 1, "popin_code": "ASSOCIATION_LIEN", "popin_label": "Association de lien"},
        {"popin_id": 2, "popin_code": "PRIMO_IDENTIFICATION", "popin_label": "Première identification"},
    ]
    return pd.DataFrame(data)


def get_event_type_id(event_type: str) -> int:
    """Map event type code to dimension ID."""
    mapping = {
        "IDENTIFICATION": 1,
        "POPIN_DISPLAYED": 2,
        "POPIN_RESPONSE": 3,
        "LINK_CREATED": 4,
        "LINK_VALIDATED": 5,
        "LINK_DELETED": 6,
        "OTHER": 7,
    }
    return mapping.get(event_type, 7)


def get_response_id(response_code: str) -> int:
    """Map response code to dimension ID."""
    mapping = {
        "ASSOCIATION": 1,
        "PEUT_ETRE": 2,
        "REFUS": 3,
        "CLOSE": 4,
    }
    return mapping.get(response_code, 0) if response_code else 0


def get_universe_id(universe_code: str) -> int:
    """Map universe code to dimension ID."""
    mapping = {
        "LBP": 1,
        "LP": 2,
        "LPM": 3,
    }
    return mapping.get(universe_code, 0) if universe_code else 0


def get_popin_id(popin_code: str) -> int:
    """Map popin code to dimension ID."""
    mapping = {
        "ASSOCIATION_LIEN": 1,
        "PRIMO_IDENTIFICATION": 2,
    }
    return mapping.get(popin_code, 0) if popin_code else 0


def create_fact_event(normalized_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create fact table from normalized DataFrame.
    
    Converts codes to foreign key IDs for dimensional model.
    """
    fact_df = normalized_df.copy()
    
    # Add surrogate key
    fact_df.insert(0, "event_sk", range(1, len(fact_df) + 1))
    
    # Add foreign keys
    fact_df["event_type_fk"] = fact_df["event_type"].apply(get_event_type_id)
    fact_df["response_fk"] = fact_df["response_code"].apply(get_response_id)
    fact_df["initial_universe_fk"] = fact_df["initial_universe"].apply(get_universe_id)
    fact_df["popin_fk"] = fact_df["popin_code"].apply(get_popin_id)
    
    # Select and reorder columns for fact table
    fact_columns = [
        "event_sk",
        "event_date",
        "event_type_fk",
        "popin_fk",
        "response_fk",
        "initial_universe_fk",
        "universe_context",
        "universe_count",
        "measure_count",
        "source_indicateur_principal",
        "source_indicateur",
        "quality_flag",
        "quality_detail",
    ]
    
    return fact_df[fact_columns]


def create_bridge_event_universe(normalized_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create bridge table for N-N relationship between events and universes.
    
    Parses universe_context to create individual relationships.
    """
    bridge_rows = []
    
    for idx, row in normalized_df.iterrows():
        event_sk = idx + 1
        universe_context = row.get("universe_context")
        
        if universe_context:
            universes = universe_context.split("|")
            for universe in universes:
                universe_id = get_universe_id(universe.strip())
                if universe_id > 0:
                    bridge_rows.append({
                        "event_sk": event_sk,
                        "universe_fk": universe_id,
                    })
    
    return pd.DataFrame(bridge_rows)


def generate_star_schema(normalized_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Generate complete star schema from normalized data.
    
    Returns:
        Dictionary mapping table names to DataFrames.
    """
    return {
        "fact_event": create_fact_event(normalized_df),
        "dim_event_type": create_dim_event_type(),
        "dim_universe": create_dim_universe(),
        "dim_response": create_dim_response(),
        "dim_popin": create_dim_popin(),
        "bridge_event_universe": create_bridge_event_universe(normalized_df),
    }


def create_zip_archive(tables: Dict[str, pd.DataFrame], format: str = "csv") -> bytes:
    """
    Create a ZIP archive containing all star schema tables.
    
    Args:
        tables: Dictionary of table name -> DataFrame
        format: Output format ('csv' or 'parquet')
    
    Returns:
        Bytes of the ZIP archive.
    """
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, df in tables.items():
            if format == "parquet":
                table_buffer = io.BytesIO()
                df.to_parquet(table_buffer, index=False, engine="pyarrow")
                zf.writestr(f"{name}.parquet", table_buffer.getvalue())
            else:
                csv_content = df.to_csv(index=False)
                zf.writestr(f"{name}.csv", csv_content)
    
    buffer.seek(0)
    return buffer.getvalue()

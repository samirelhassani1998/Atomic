# Atomic - Data Normalization App

A Streamlit application that normalizes aggregated data files containing composite fields into a clean, tidy format.

## 🚀 Live App

**URL**: [https://atomic-z7dyvdfqm22jr2n2hlcqwr.streamlit.app/](https://atomic-z7dyvdfqm22jr2n2hlcqwr.streamlit.app/)

## 📋 Features

- Upload CSV or Parquet files
- Auto-detect measure and date columns
- Normalize composite `Indicateur_principal` and `indicateur` fields
- Export as:
  - **MVP Tidy**: Single normalized CSV/Parquet file
  - **Star Schema**: ZIP archive with dimensional model

## 🖥️ Local Development

```bash
# Clone the repository
git clone https://github.com/samirelhassani1998/Atomic.git
cd Atomic

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

## 📥 Input Format

Your file must contain these columns:

| Column | Required | Description |
|--------|----------|-------------|
| `Indicateur_principal` | ✅ | Event type identifier |
| `indicateur` | ✅ | Detail value (universe, response, etc.) |
| `valeur` / `count` | ❌ | Measure value (defaults to 1) |
| `date` / `periode` | ❌ | Date/period value |

## 🔄 Column Normalization

The app automatically normalizes column names to handle case variations and common aliases.

### Supported Aliases

| Input Column | → Normalized |
|--------------|--------------|
| `Indicateur_Principal` | `Indicateur_principal` |
| `indicateur_principal` | `Indicateur_principal` |
| `Indicateur-Principal` | `Indicateur_principal` |
| `indicateur principal` | `Indicateur_principal` |

All column names are also:
- Trimmed of leading/trailing whitespace
- Normalized by replacing spaces and hyphens with underscores

If any columns are auto-mapped, a notification appears in the UI:
> 🔄 **Colonnes auto-mappées :** `Indicateur_Principal` → `Indicateur_principal`

## 📤 Output Structure

### MVP Tidy (`normalized_events.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `event_date` | nullable | Date/period from source |
| `event_type` | ENUM | IDENTIFICATION, POPIN_DISPLAYED, POPIN_RESPONSE, LINK_CREATED, LINK_VALIDATED, LINK_DELETED, OTHER |
| `popin_code` | nullable | Pop-in type code |
| `response_code` | nullable ENUM | ASSOCIATION, PEUT_ETRE, REFUS, CLOSE |
| `initial_universe` | nullable ENUM | LBP, LP, LPM |
| `universe_context` | nullable | Pipe-separated universes (e.g., "LBP\|LPM") |
| `universe_count` | int | Number of universes in context |
| `measure_count` | int | Value from measure column |
| `source_indicateur_principal` | string | Original value (traceability) |
| `source_indicateur` | string | Original value (traceability) |
| `quality_flag` | ENUM | OK, WARNING, ERROR |
| `quality_detail` | string | Quality issue description |

### Star Schema (ZIP)

- `fact_event.csv` - Fact table with FK references
- `dim_event_type.csv` - Event type dimension
- `dim_universe.csv` - Universe dimension (LBP, LP, LPM)
- `dim_response.csv` - Response code dimension
- `dim_popin.csv` - Pop-in type dimension
- `bridge_event_universe.csv` - N-N relationship bridge

## 🔄 Mapping Rules

### Event Type Mapping

| Indicateur_principal | → event_type |
|---------------------|--------------|
| `Identification` | IDENTIFICATION |
| `Popin` | POPIN_DISPLAYED |
| `Primo_Identification_Popin` | POPIN_DISPLAYED |
| `Creation_Lien` | LINK_CREATED |
| `Validation_Lien` | LINK_VALIDATED |
| `Suppression_Lien` | LINK_DELETED |
| `ReponsePopin_*` | POPIN_RESPONSE |

### Universe Context Extraction

`ReponsePopin_LBP_LPM` → `universe_context="LBP|LPM"`, `universe_count=2`

### Response Code Normalization

| Input | → response_code |
|-------|-----------------|
| Peut-être | PEUT_ETRE |
| Association | ASSOCIATION |
| Refus | REFUS |
| Close / Fermer | CLOSE |

## 📄 License

Apache 2.0
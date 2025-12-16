"""
Streamlit Data Normalization App

A tool for normalizing aggregated data files containing composite fields
into a clean, tidy format with proper separation of concerns.
"""

import io
import pandas as pd
import streamlit as st

from services.normalizer import normalize_dataframe, get_quality_summary
from services.schema import generate_star_schema, create_zip_archive
from utils.mappings import MEASURE_COLUMN_CANDIDATES, DATE_COLUMN_CANDIDATES


# Page configuration
st.set_page_config(
    page_title="Normalize Data",
    page_icon="🔄",
    layout="wide",
)


def detect_columns(df: pd.DataFrame, candidates: list) -> list:
    """Auto-detect columns matching candidate names."""
    columns = df.columns.str.lower().tolist()
    matches = []
    for candidate in candidates:
        for col in df.columns:
            if candidate in col.lower():
                matches.append(col)
    return list(dict.fromkeys(matches))  # Remove duplicates while preserving order


def load_file(uploaded_file) -> pd.DataFrame:
    """Load uploaded file as DataFrame."""
    file_name = uploaded_file.name.lower()
    
    if file_name.endswith(".parquet"):
        return pd.read_parquet(uploaded_file, engine="pyarrow")
    elif file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {file_name}")


def main():
    # Header
    st.title("🔄 Normalize Data")
    st.markdown("""
    Transform aggregated data with composite fields into a clean, normalized format.
    
    **Required columns**: `Indicateur_principal`, `indicateur`  
    **Optional columns**: date/period, measure/count
    """)
    
    st.divider()
    
    # File upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📁 Upload your data file",
            type=["csv", "parquet"],
            help="Upload a CSV or Parquet file containing aggregated data"
        )
    
    if uploaded_file is None:
        st.info("👆 Please upload a file to begin normalization.")
        
        # Show example input format
        with st.expander("📋 Expected input format"):
            st.markdown("""
            Your file should contain at minimum these columns:
            
            | Indicateur_principal | indicateur | valeur (optional) |
            |---------------------|------------|-------------------|
            | Identification | LBP | 100 |
            | ReponsePopin_LBP_LPM | Association | 50 |
            | Creation_Lien | LP | 25 |
            | Popin | LP | 75 |
            """)
        return
    
    # Load and validate file
    try:
        df = load_file(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        return
    
    # Validate required columns
    required_cols = ["Indicateur_principal", "indicateur"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"❌ Missing required columns: {missing_cols}")
        st.write("**Available columns:**", list(df.columns))
        return
    
    # Show input preview
    st.subheader("📥 Input Data Preview")
    col_preview, col_stats = st.columns([3, 1])
    
    with col_preview:
        st.dataframe(df.head(10), use_container_width=True)
    
    with col_stats:
        st.metric("Total Rows", len(df))
        st.metric("Columns", len(df.columns))
    
    st.divider()
    
    # Configuration section
    st.subheader("⚙️ Configuration")
    
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        # Detect measure columns
        measure_candidates = detect_columns(df, MEASURE_COLUMN_CANDIDATES)
        measure_options = ["(none - use default: 1)"] + measure_candidates + [c for c in df.columns if c not in measure_candidates]
        
        measure_col = st.selectbox(
            "📊 Measure column",
            options=measure_options,
            help="Column containing count/value data"
        )
        if measure_col == "(none - use default: 1)":
            measure_col = None
    
    with config_col2:
        # Detect date columns
        date_candidates = detect_columns(df, DATE_COLUMN_CANDIDATES)
        date_options = ["(none)"] + date_candidates + [c for c in df.columns if c not in date_candidates]
        
        date_col = st.selectbox(
            "📅 Date column",
            options=date_options,
            help="Column containing date/period data"
        )
        if date_col == "(none)":
            date_col = None
    
    with config_col3:
        output_format = st.selectbox(
            "📦 Output format",
            options=["MVP tidy (1 fichier)", "Star schema (zip)"],
            help="Choose output format"
        )
    
    st.divider()
    
    # Run normalization button
    if st.button("🚀 Run Normalization", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                # Normalize data
                normalized_df = normalize_dataframe(df, measure_col, date_col)
                
                # Store in session state
                st.session_state["normalized_df"] = normalized_df
                st.session_state["output_format"] = output_format
                
                st.success("✅ Normalization complete!")
                
            except Exception as e:
                st.error(f"❌ Normalization error: {e}")
                return
    
    # Display results if available
    if "normalized_df" in st.session_state:
        normalized_df = st.session_state["normalized_df"]
        output_format = st.session_state.get("output_format", "MVP tidy (1 fichier)")
        
        st.subheader("📤 Output Preview")
        
        # Quality summary
        quality = get_quality_summary(normalized_df)
        
        q_col1, q_col2, q_col3, q_col4 = st.columns(4)
        with q_col1:
            st.metric("Output Rows", quality["total_rows"])
        with q_col2:
            st.metric("✅ OK", f"{quality['ok_count']} ({quality['ok_pct']}%)")
        with q_col3:
            st.metric("⚠️ Warnings", f"{quality['warning_count']} ({quality['warning_pct']}%)")
        with q_col4:
            st.metric("❌ Errors", f"{quality['error_count']} ({quality['error_pct']}%)")
        
        # Show normalized data preview
        st.dataframe(normalized_df.head(20), use_container_width=True)
        
        # Show quality issues if any
        issues_df = normalized_df[normalized_df["quality_flag"] != "OK"]
        if len(issues_df) > 0:
            with st.expander(f"🔍 View Quality Issues ({len(issues_df)} rows)"):
                st.dataframe(
                    issues_df[["source_indicateur_principal", "source_indicateur", "quality_flag", "quality_detail"]],
                    use_container_width=True
                )
        
        st.divider()
        
        # Download section
        st.subheader("💾 Download")
        
        download_col1, download_col2 = st.columns(2)
        
        if "Star schema" in output_format:
            # Generate star schema
            with st.spinner("Generating star schema..."):
                tables = generate_star_schema(normalized_df)
                zip_bytes = create_zip_archive(tables, format="csv")
            
            with download_col1:
                st.download_button(
                    label="📥 Download Star Schema (ZIP)",
                    data=zip_bytes,
                    file_name="star_schema.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
            
            # Show table list
            with st.expander("📋 Star Schema Tables"):
                for name, table_df in tables.items():
                    st.markdown(f"**{name}** ({len(table_df)} rows)")
                    st.dataframe(table_df.head(5), use_container_width=True)
        else:
            # MVP tidy output
            csv_data = normalized_df.to_csv(index=False)
            parquet_buffer = io.BytesIO()
            normalized_df.to_parquet(parquet_buffer, index=False, engine="pyarrow")
            parquet_data = parquet_buffer.getvalue()
            
            with download_col1:
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name="normalized_events.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            
            with download_col2:
                st.download_button(
                    label="📥 Download Parquet",
                    data=parquet_data,
                    file_name="normalized_events.parquet",
                    mime="application/octet-stream",
                    use_container_width=True,
                )


if __name__ == "__main__":
    main()

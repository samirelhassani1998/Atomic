"""
Tests for column normalization utilities.
"""

import pandas as pd
import pytest

from utils.columns import (
    normalize_columns,
    clean_column_name,
    get_missing_required_columns,
    format_column_mapping_message,
)


class TestCleanColumnName:
    """Tests for clean_column_name function."""

    def test_trim_whitespace(self):
        assert clean_column_name("  column  ") == "column"

    def test_replace_spaces_with_underscore(self):
        assert clean_column_name("my column") == "my_column"

    def test_replace_hyphens_with_underscore(self):
        assert clean_column_name("my-column") == "my_column"

    def test_replace_multiple_separators(self):
        assert clean_column_name("my - column") == "my_column"


class TestNormalizeColumns:
    """Tests for normalize_columns function."""

    def test_uppercase_principal_normalized(self):
        """Indicateur_Principal (capital P) should be normalized to Indicateur_principal."""
        df = pd.DataFrame({
            "Indicateur_Principal": ["value1"],
            "indicateur": ["value2"],
            "nombre": [100],
        })
        
        result_df, mapping = normalize_columns(df)
        
        assert "Indicateur_principal" in result_df.columns
        assert "Indicateur_Principal" not in result_df.columns
        assert mapping.get("Indicateur_Principal") == "Indicateur_principal"

    def test_already_correct_no_change(self):
        """Already correct Indicateur_principal should not be changed (no regression)."""
        df = pd.DataFrame({
            "Indicateur_principal": ["value1"],
            "indicateur": ["value2"],
        })
        
        result_df, mapping = normalize_columns(df)
        
        assert "Indicateur_principal" in result_df.columns
        # Should not be in mapping since no change was needed
        assert "Indicateur_principal" not in mapping

    def test_other_columns_unchanged(self):
        """Other columns like indicateur, nombre, usageDate should remain accessible."""
        df = pd.DataFrame({
            "Indicateur_Principal": ["value1"],
            "indicateur": ["value2"],
            "nombre": [100],
            "usageDate": ["2024-01-01"],
        })
        
        result_df, mapping = normalize_columns(df)
        
        assert "indicateur" in result_df.columns
        assert "nombre" in result_df.columns
        assert "usageDate" in result_df.columns

    def test_all_lowercase_normalized(self):
        """indicateur_principal (all lowercase) should be normalized."""
        df = pd.DataFrame({
            "indicateur_principal": ["value1"],
            "indicateur": ["value2"],
        })
        
        result_df, mapping = normalize_columns(df)
        
        assert "Indicateur_principal" in result_df.columns

    def test_hyphen_variant_normalized(self):
        """Indicateur-Principal should be normalized."""
        df = pd.DataFrame({
            "Indicateur-Principal": ["value1"],
            "indicateur": ["value2"],
        })
        
        result_df, mapping = normalize_columns(df)
        
        assert "Indicateur_principal" in result_df.columns


class TestGetMissingRequiredColumns:
    """Tests for get_missing_required_columns function."""

    def test_all_present(self):
        df = pd.DataFrame({
            "Indicateur_principal": ["value1"],
            "indicateur": ["value2"],
        })
        
        missing = get_missing_required_columns(df, ["Indicateur_principal", "indicateur"])
        
        assert missing == []

    def test_case_insensitive_match(self):
        df = pd.DataFrame({
            "indicateur_principal": ["value1"],
            "INDICATEUR": ["value2"],
        })
        
        missing = get_missing_required_columns(df, ["Indicateur_principal", "indicateur"])
        
        assert missing == []

    def test_missing_column(self):
        df = pd.DataFrame({
            "indicateur": ["value2"],
        })
        
        missing = get_missing_required_columns(df, ["Indicateur_principal", "indicateur"])
        
        assert "Indicateur_principal" in missing


class TestFormatColumnMappingMessage:
    """Tests for format_column_mapping_message function."""

    def test_empty_mapping(self):
        result = format_column_mapping_message({})
        assert result == ""

    def test_single_mapping(self):
        result = format_column_mapping_message({"Indicateur_Principal": "Indicateur_principal"})
        assert "Indicateur_Principal" in result
        assert "Indicateur_principal" in result
        assert "→" in result

    def test_multiple_mappings(self):
        result = format_column_mapping_message({
            "col1": "COL1",
            "col2": "COL2",
        })
        assert "col1" in result
        assert "col2" in result

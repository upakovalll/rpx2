"""
Pricing sheet builder for the 87-column audit format.
Handles the complex mapping from database fields to Excel columns.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import logging

from ..base import ExcelSheet
from ..formatters import ExcelFormatter, DataProcessor
from ..column_definitions import (
    AUDIT_COLUMN_ORDER,
    COLUMN_MAPPING,
    COLUMN_TRANSFORMATIONS,
    BASIS_POINTS_COLUMNS,
    PERCENTAGE_COLUMNS
)

logger = logging.getLogger(__name__)


class PricingSheet:
    """Builder for pricing data sheets in the 87-column audit format."""
    
    @staticmethod
    def create_from_loans(loans_data: List[Dict[str, Any]]) -> ExcelSheet:
        """
        Create a pricing sheet from loan data.
        
        Args:
            loans_data: List of loan records from database
            
        Returns:
            ExcelSheet configured with pricing data
        """
        df = PricingSheet._format_pricing_data(loans_data)
        return ExcelSheet('Loans', df, ExcelFormatter.format_worksheet)
    
    @staticmethod
    def create_from_pricing_data(pricing_data: List[Dict[str, Any]]) -> ExcelSheet:
        """
        Create a pricing sheet from pricing engine output.
        
        Args:
            pricing_data: List of pricing records from v_pricing_engine_output
            
        Returns:
            ExcelSheet configured with pricing data
        """
        df = PricingSheet._format_pricing_data(pricing_data)
        return ExcelSheet('Pricing Results', df, ExcelFormatter.format_worksheet)
    
    @staticmethod
    def _format_pricing_data(pricing_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Format pricing data into the 87-column audit format.
        
        Args:
            pricing_data: Raw pricing data from database
            
        Returns:
            DataFrame with exactly 87 columns in the correct order
        """
        if not pricing_data:
            # Return empty DataFrame with unique column names for positions
            columns = []
            for i, col in enumerate(AUDIT_COLUMN_ORDER, 1):
                # Add position suffix to make columns unique
                columns.append(f"{col}__pos{i:02d}")
            return pd.DataFrame(columns=columns)
        
        # Convert to DataFrame
        df = pd.DataFrame(pricing_data)
        
        # Apply safe value conversion to all columns
        for col in df.columns:
            df[col] = df[col].apply(ExcelFormatter.safe_value)
        
        # Create result DataFrame with 87 columns using position-based unique names
        result = pd.DataFrame()
        
        # Map each of the 87 columns with unique position identifiers
        for i, excel_col in enumerate(AUDIT_COLUMN_ORDER, 1):
            # Use position suffix to ensure uniqueness
            unique_col_name = f"{excel_col}__pos{i:02d}"
            result[unique_col_name] = PricingSheet._map_column(df, excel_col, position=i)
        
        # Apply data type conversions (using the original column names)
        result = PricingSheet._apply_data_conversions(result)
        
        return result
    
    @staticmethod
    def _map_column(source_df: pd.DataFrame, excel_column: str, position: int = None) -> pd.Series:
        """
        Map a single Excel column from source data.
        
        Args:
            source_df: Source DataFrame with database fields
            excel_column: Target Excel column name
            position: Column position (1-based) to distinguish duplicate column names
            
        Returns:
            Series with mapped values for the column
        """
        # Check if there's a special transformation for this column
        if excel_column in COLUMN_TRANSFORMATIONS:
            transform_func = COLUMN_TRANSFORMATIONS[excel_column]
            return source_df.apply(transform_func, axis=1)
        
        # Handle special cases BEFORE checking general mapping
        # This is important for columns like 'Accrued Interest' that appear twice
        if excel_column == 'Accrued Interest':
            # Distinguish between column 33 and column 36
            if position == 33:
                # Column 33: Maps to accrued_interest field (dollar amount)
                if 'accrued_interest' in source_df.columns:
                    return source_df['accrued_interest']
                return 0
            elif position == 36:
                # Column 36: Maps to price_accrued_pct field (percentage)
                # BookMainReport expects this as decimal (0.00479 for 0.479%)
                if 'price_accrued_pct' in source_df.columns:
                    # Divide by 100 to convert from percentage to decimal format
                    return source_df['price_accrued_pct'] / 100
                return 0
            else:
                # Fallback - default to accrued_interest
                if 'accrued_interest' in source_df.columns:
                    return source_df['accrued_interest']
                return 0
        
        if excel_column == 'Contract Type':
            # Contract Type is derived from interest_type
            if 'interest_type' in source_df.columns:
                return source_df['interest_type']
            return ''
        
        if excel_column == 'Maturity Assumption':
            if 'calculated_maturity_assumption' in source_df.columns:
                return source_df['calculated_maturity_assumption']
            return 'Maturity'
        
        if excel_column == 'Credit Spread (bps)':
            # Use rpx_base_spread_bps or effective_credit_spread
            if 'rpx_base_spread_bps' in source_df.columns:
                return source_df['rpx_base_spread_bps']
            elif 'effective_credit_spread' in source_df.columns:
                return source_df['effective_credit_spread']
            return 0
        
        if excel_column == 'Market Yield':
            if 'market_yield_cbe' in source_df.columns:
                return source_df['market_yield_cbe']
            return 0
        
        # Now check general mapping (after special cases)
        # Find the database field that maps to this Excel column
        db_field = None
        for field, col_name in COLUMN_MAPPING.items():
            if col_name == excel_column:
                db_field = field
                break
        
        # If we found a direct mapping, use it
        if db_field and db_field in source_df.columns:
            return source_df[db_field]
        
        # Placeholder columns that don't have data yet
        if excel_column in [
            'Lower Fair Value Range - Price',
            'Upper Fair Value Range - Price',
            'Lower Fair Value Range - FV',
            'Upper Fair Value Range - FV',
            'Lower Fair Value Range - MEY',
            'Upper Fair Value Range - MEY'
        ]:
            return None
        
        # Delta columns (changes)
        if excel_column.startswith('Δ'):
            return None  # These would need historical data
        
        # Prior period columns
        if 'Prior' in excel_column:
            return None  # These would need historical data
        
        # Other placeholder columns
        if excel_column in ['CS', 'MY', 'MS', 'Yield Curve Shift', 'Yield Curve Roll', 
                             'Prior Scenario', 'New Loan to Portfolio?']:
            return None
        
        # If no mapping found, return None
        return None
    
    @staticmethod
    def _apply_data_conversions(df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply data type conversions for specific columns.
        
        Args:
            df: DataFrame with mapped columns (columns have __posXX suffixes)
            
        Returns:
            DataFrame with converted data types
        """
        # Map original column names to their position-based names
        col_mapping = {}
        for col in df.columns:
            # Extract the original column name (remove __posXX suffix)
            if '__pos' in col:
                original_name = col.rsplit('__pos', 1)[0]
                col_mapping[original_name] = col
        
        # Convert numeric columns
        # Note: 'Accrued Interest' appears twice but at different positions with different meanings
        # Column 33: Dollar amount, Column 36: Percentage - handled separately
        numeric_cols = [
            'Original Balance', 'Current Balance - Includes Accrued Interest & PIK Interest', 'PIK Balance',
            'Fair Value', 'Fair Value + Accrued Interest',
            'EAD', 'WAL (yrs)', 'Modified Duration (yrs)', 'Convexity',
            'Client % of Total Loan Facility'
        ]
        
        for original_col in numeric_cols:
            if original_col in col_mapping:
                col = col_mapping[original_col]
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert percentage columns (ensure they're decimals)
        for original_col in PERCENTAGE_COLUMNS:
            if original_col in col_mapping:
                col = col_mapping[original_col]
                # If values are > 1, they're likely already percentages, divide by 100
                mask = df[col] > 1
                df.loc[mask, col] = df.loc[mask, col] / 100
        
        # Basis points columns stay as-is (already in bps)
        
        # Ensure date columns are properly formatted
        date_cols = [
            'Default Date', 'Loan Origination Date', 'Original Maturity Date',
            'Maturity', 'Extension 1st', 'Extension 2nd',
            'Extension 3rd'
        ]
        
        for original_col in date_cols:
            if original_col in col_mapping:
                col = col_mapping[original_col]
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Integer columns
        int_cols = ['Loan ID', 'Lag to Recovery']
        for original_col in int_cols:
            if original_col in col_mapping:
                col = col_mapping[original_col]
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
        return df
    
    @staticmethod
    def validate_column_count(df: pd.DataFrame) -> bool:
        """
        Validate that the DataFrame has exactly 87 columns.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid, raises exception otherwise
        """
        column_count = len(df.columns)
        if column_count != 87:
            logger.error(f"Expected 87 columns, got {column_count}")
            missing = set(AUDIT_COLUMN_ORDER) - set(df.columns)
            extra = set(df.columns) - set(AUDIT_COLUMN_ORDER)
            if missing:
                logger.error(f"Missing columns: {missing}")
            if extra:
                logger.error(f"Extra columns: {extra}")
            raise ValueError(f"Column count mismatch: expected 87, got {column_count}")
        return True
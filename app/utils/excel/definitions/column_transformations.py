"""
Special column transformations for Excel export.
These handle columns that require custom mapping logic.
"""

# Special column mappings that require transformation
# Each key is an Excel column name, value is a lambda function that transforms the row
COLUMN_TRANSFORMATIONS = {
    # Contract Type is derived from interest_type field
    'Contract Type': lambda row: row.get('interest_type', ''),
    
    # Maturity Assumption comes from calculated field or default
    'Maturity Assumption': lambda row: row.get('calculated_maturity_assumption', 'Maturity'),
    
    # Credit Spread without (bps) - using display_credit_spread which is already properly formatted
    'Credit Spread': lambda row: row.get('display_credit_spread', row.get('effective_credit_spread', 0)),
    
    # Market Yield with full name
    'Market Yield (or Discount Rate)': lambda row: row.get('market_yield_cbe', 0),
    
    # Component Yield with typo preserved
    'Conponent Yield': lambda row: row.get('component_yield_decimal', row.get('component_yield_pct', 0)),
    
    # Property Lifecycle Financing - full name
    'Property Lifecycle Financing': lambda row: row.get('property_lifecycle_financing', 'Permanent'),
    
    # Client % of Total Loan Facility
    'Client % of Total Loan Facility': lambda row: row.get('client_percentage', row.get('client_pct', 0)),
    
    # Price fields with updated names
    'Price': lambda row: row.get('price_clean_pct', row.get('price_clean_decimal', 0) * 100 if row.get('price_clean_decimal', 0) < 1 else row.get('price_clean_decimal', 0)),
    
    'Price including Accrued': lambda row: row.get('price_dirty_pct', row.get('price_dirty_decimal', 0) * 100 if row.get('price_dirty_decimal', 0) < 1 else row.get('price_dirty_decimal', 0)),
    
    # Note: Accrued Interest columns handled specially in pricing_sheet.py based on position
    # Column 33: accrued_interest (dollar amount)
    # Column 36: price_accrued_pct (percentage)
    
    # LTV and DSCR need to be strings in Excel
    'LTV': lambda row: str(row.get('ltv_current', '')) if row.get('ltv_current') is not None else '',
    'DSCR': lambda row: str(row.get('dscr_current', '')) if row.get('dscr_current') is not None else '',
    'LTV Prior': lambda row: str(row.get('ltv_prior', '')) if row.get('ltv_prior') is not None else '',
    'DSCR Prior': lambda row: str(row.get('dscr_prior', '')) if row.get('dscr_prior') is not None else '',
}

# Columns that need placeholder values when missing
# Add column 47 with double space
COLUMN_TRANSFORMATIONS['Upper  Fair Value Range - FV'] = lambda row: row.get('upper_fair_value_fv', None)

PLACEHOLDER_COLUMNS = {
    # Fair value range columns - not yet implemented
    'Lower Fair Value Range - Price': None,
    'Upper Fair Value Range - Price': None,
    'Lower Fair Value Range - FV': None,
    'Upper Fair Value Range - FV': None,
    'Lower Fair Value Range - MEY': None,
    'Upper Fair Value Range - MEY': None,
    
    # Delta columns - require historical data
    'Δ Price': None,
    'Δ Price due to Yield CBE': None,
    'Δ Price due to Credit Spread / DM': None,
    'Δ Price due to Benchmark': None,
    'Δ Price due to Yield Curve Shift': None,
    'Δ Price due to Yield Curve Roll': None,
    'Δ Price due to Accretion to Par or Amortization of Premium': None,
    'Δ Credit Spread': None,
    'Δ Benchmark Yld': None,
    'Δ CBE Yield': None,
    
    # Yield curve columns
    'Yield Curve Shift': None,
    'Yield Curve Roll': None,
    
    # Prior period columns - require historical data
    'Current Balance Prior': None,
    'Price Prior': None,
    'Benchmark Yield Prior': None,
    'Credit Spread Prior': None,
    'Market Yield Prior': None,
    'DSCR Prior': None,
    'LTV Prior': None,
    'WAL Prior': None,
    'Duration Prior': None,
    'Loan Status Prior': None,
    'Prior Scenario': None,
    
    # Other placeholders
    'CS': None,
    'MY': None,
    'MS': None,
    'New Loan to Portfolio?': None
}

def transform_column_value(excel_column: str, row_data: dict):
    """
    Apply transformation for a specific column if needed.
    
    Args:
        excel_column: The Excel column name
        row_data: Dictionary of row data from database
        
    Returns:
        Transformed value or None if no transformation exists
    """
    if excel_column in COLUMN_TRANSFORMATIONS:
        return COLUMN_TRANSFORMATIONS[excel_column](row_data)
    elif excel_column in PLACEHOLDER_COLUMNS:
        return PLACEHOLDER_COLUMNS[excel_column]
    return None

def needs_transformation(excel_column: str) -> bool:
    """Check if a column needs special transformation."""
    return excel_column in COLUMN_TRANSFORMATIONS or excel_column in PLACEHOLDER_COLUMNS
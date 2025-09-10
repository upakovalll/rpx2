"""
Data type classifications for Excel columns.
These definitions help with proper formatting and data conversion.
"""

# Numeric columns that need special handling
NUMERIC_COLUMNS = [
    'Original Balance', 
    'Current Balance - Includes Accrued Interest & PIK Interest', 
    'PIK Balance',
    'Fair Value', 
    'Fair Value + Accrued Interest', 
    'Accrued Interest',
    'NPV', 
    'Gross Proceeds', 
    'Net Proceeds', 
    'EAD',
    'WAL (yrs)', 
    'Modified Duration (yrs)', 
    'Convexity',
    # Note: LTV and DSCR removed - they're strings
    'Client % of Total Loan Facility',
    'Current Balance Prior'
]

# Currency columns (subset of numeric, for specific formatting)
CURRENCY_COLUMNS = [
    'Original Balance',
    'Current Balance',
    'PIK Balance',
    'Fair Value',
    'Fair Value + Accrued',
    'Accrued Interest',
    'NPV',
    'Gross Proceeds',
    'Net Proceeds',
    'EAD',
    'Current Balance Prior',
    'Lower Fair Value Range - FV',
    'Upper Fair Value Range - FV'
]

# Percentage columns (stored as decimals, displayed as percentages)
PERCENTAGE_COLUMNS = [
    'PD', 
    'LGD', 
    'CDR', 
    'Price', 
    'Price including Accrued', 
    'Accrued Interest',  # Column 36
    'Market Yield (or Discount Rate)', 
    'Benchmark Yield | Index Rate', 
    'Conponent Yield',
    'Client % of Total Loan Facility',
    'Price Prior',
    'Market Yield Prior',
    'Lower Fair Value Range - Price',
    'Upper Fair Value Range - Price',
    'Lower Fair Value Range - MEY',
    'Upper Fair Value Range - MEY'
]

# Basis points columns (stored as bps, may need conversion)
BASIS_POINTS_COLUMNS = [
    'Credit Spread',  # No longer has (bps) suffix
    'Total Spread (bps)', 
    'DMor Spread (bps)',
    'Effective Spread', 
    'Credit Spread Prior',
    'Δ Credit Spread'
]

# Date columns
DATE_COLUMNS = [
    'Default Date', 
    'Loan Origination Date', 
    'Original Maturity Date', 
    'Maturity',  # Was 'Effective Maturity'
    'Extension 1st', 
    'Extension 2nd', 
    'Extension 3rd', 
    'Valuation Date', 
    'Settlement Date',
    'IO End Date'
]

# Integer columns
INTEGER_COLUMNS = [
    'Loan ID', 
    'Lag to Recovery'
]

# Text/String columns (no special formatting needed)
TEXT_COLUMNS = [
    'Client Loan Number',
    'Loan Name',
    'Pricing Scenario',
    'Sector',
    'Property Type',
    'Property Lifecycle Financing',
    'Property Location',
    'Sponsor/Borrower',
    'Currency',
    'Position in Capital Stack',
    'Periodicity',
    'Interest Day Count',
    'Loan Status',
    'Propoerty & Loan Commentary',  # Intentional typo
    'Coupon Description',
    'Contract Type',
    'Interest Type',
    'Amortization Type',
    'Loss Scenario',
    'Default Scenario',
    'Becnhmark',  # Intentional typo
    'Maturity Assumption',
    'Prior Scenario',
    'CS',
    'MY',
    'MS',
    'Loan Status Prior',
    'New Loan to Portfolio?',
    # LTV and DSCR are strings in Excel
    'LTV',
    'DSCR',
    'LTV Prior',
    'DSCR Prior'
]

# Columns that may need special null handling
NULLABLE_COLUMNS = [
    'Commentary',
    'Coupon Description',
    'Default Date',
    'Default Scenario',
    'PIK Balance',
    'Extension 1st',
    'Extension 2nd',
    'Extension 3rd',
    'Lower Fair Value Range - Price',
    'Upper Fair Value Range - Price',
    'Lower Fair Value Range - FV',
    'Upper Fair Value Range - FV',
    'Lower Fair Value Range - MEY',
    'Upper Fair Value Range - MEY',
    'Δ Price',
    'Δ Price due to Yield CBE',
    'Δ Price due to Credit Spread / DM',
    'Δ Price due to Benchmark',
    'Δ Price due to Yield Curve Shift',
    'Δ Price due to Yield Curve Roll',
    'Δ Price due to Accretion to Par or Amortization of Premium',
    'Δ Credit Spread',
    'Δ Benchmark Yld',
    'Δ CBE Yield',
    'Yield Curve Shift',
    'Yield Curve Roll',
    'Prior Scenario',
    'CS',
    'MY',
    'MS',
    'Current Balance Prior',
    'Price Prior',
    'Benchmark Yield Prior',
    'Credit Spread Prior',
    'Market Yield Prior',
    'DSCR Prior',
    'LTV Prior',
    'WAL Prior',
    'Duration Prior',
    'Loan Status Prior',
    'New Loan to Portfolio?'
]

def get_column_type(column_name: str) -> str:
    """
    Determine the data type category for a column.
    
    Returns:
        One of: 'currency', 'percentage', 'basis_points', 'date', 'integer', 'numeric', 'text'
    """
    if column_name in CURRENCY_COLUMNS:
        return 'currency'
    elif column_name in PERCENTAGE_COLUMNS:
        return 'percentage'
    elif column_name in BASIS_POINTS_COLUMNS:
        return 'basis_points'
    elif column_name in DATE_COLUMNS:
        return 'date'
    elif column_name in INTEGER_COLUMNS:
        return 'integer'
    elif column_name in NUMERIC_COLUMNS:
        return 'numeric'
    else:
        return 'text'
"""
Logical groupings of columns for easier management and reference.
These groups help locate related columns quickly.
"""

# Group columns by category for easier management
COLUMN_GROUPS = {
    'identifiers': [
        'Loan ID', 
        'Client Loan #', 
        'Loan Name', 
        'Pricing Scenario'
    ],
    
    'property': [
        'Sector', 
        'Property Type', 
        'Property Lifecycle', 
        'Property Location'
    ],
    
    'borrower': [
        'Borrower', 
        'Client %'
    ],
    
    'balances': [
        'Original Balance', 
        'Current Balance', 
        'PIK Balance', 
        'Currency'
    ],
    
    'structure': [
        'Position in Capital Stack', 
        'Periodicity', 
        'Day Count', 
        'Loan Status',
        'Interest Type', 
        'Contract Type', 
        'Amortization Type'
    ],
    
    'pricing': [
        'Fair Value', 
        'Fair Value + Accrued', 
        'Accrued Interest',
        'Price %', 
        'Price + Accrued %', 
        'Accrued %'
    ],
    
    'yields': [
        'Market Yield', 
        'Benchmark Yield', 
        'Component Yield', 
        'Benchmark'
    ],
    
    'spreads': [
        'Credit Spread (bps)', 
        'Total Spread (bps)', 
        'DMor Spread (bps)', 
        'Effective Spread'
    ],
    
    'risk': [
        'PD', 
        'EAD', 
        'LGD', 
        'Lag to Recovery', 
        'CDR', 
        'Loss Scenario',
        'Default Date', 
        'Default Scenario'
    ],
    
    'metrics': [
        'WAL (years)', 
        'Modified Duration', 
        'Convexity', 
        'LTV', 
        'DSCR'
    ],
    
    'dates': [
        'Origination Date', 
        'Original Maturity', 
        'Effective Maturity',
        'Extension 1st', 
        'Extension 2nd', 
        'Extension 3rd'
    ],
    
    'changes': [
        'Δ Price', 
        'Δ Price due to Yield CBE', 
        'Δ Price due to Credit Spread / DM',
        'Δ Price due to Benchmark', 
        'Δ Credit Spread', 
        'Δ Benchmark Yld', 
        'Δ CBE Yield'
    ],
    
    'prior_period': [
        'Current Balance Prior', 
        'Price Prior', 
        'Benchmark Yield Prior',
        'Credit Spread Prior', 
        'Market Yield Prior', 
        'DSCR Prior', 
        'LTV Prior', 
        'WAL Prior', 
        'Duration Prior', 
        'Loan Status Prior'
    ],
    
    'fair_value_ranges': [
        'Lower Fair Value Range - Price',
        'Upper Fair Value Range - Price',
        'Lower Fair Value Range - FV',
        'Upper Fair Value Range - FV',
        'Lower Fair Value Range - MEY',
        'Upper Fair Value Range - MEY'
    ],
    
    'miscellaneous': [
        'Commentary',
        'Coupon Description',
        'Maturity Assumption',
        'Prior Scenario',
        'CS',
        'MY',
        'MS',
        'Yield Curve Shift',
        'Yield Curve Roll',
        'New Loan to Portfolio?'
    ]
}

def get_columns_in_group(group_name: str) -> list:
    """Get all columns in a specific group."""
    return COLUMN_GROUPS.get(group_name, [])
"""
The exact 87-column order for audit format Excel exports.
Each column is numbered with its position for easy reference.
"""

# The exact 87-column order for audit format
# DO NOT MODIFY THE ORDER - positions are critical for audit compliance
AUDIT_COLUMN_ORDER = [
    # Columns 1-10: Core identifiers and scenarios
    'Loan ID',                           # 1
    'Pricing Scenario',                  # 2
    'Maturity Assumption',               # 3
    'Credit Spread',                      # 4
    'Market Yield (or Discount Rate)',  # 5
    'Loss Scenario',                     # 6
    'PD',                                # 7
    'EAD',                               # 8
    'LGD',                               # 9
    'Lag to Recovery',                   # 10
    
    # Columns 11-20: Default and loan details
    'Default Date',                      # 11
    'CDR',                               # 12
    'Client Loan Number',               # 13
    'Loan Name',                         # 14
    'Sector',                            # 15
    'Property Type',                     # 16
    'Property Lifecycle Financing',     # 17
    'Sponsor/Borrower',                 # 18
    'Original Balance',                  # 19
    'Current Balance - Includes Accrued Interest & PIK Interest',  # 20
    
    # Columns 21-30: Currency and loan structure
    'Currency',                          # 21
    'Client % of Total Loan Facility',   # 22
    'PIK Balance',                       # 23
    'Position in Capital Stack',         # 24
    'Periodicity',                       # 25
    'Interest Day Count',                # 26
    'Loan Status',                       # 27
    'Propoerty & Loan Commentary',       # 28  # Note: Intentional typo 'Propoerty'
    'Coupon Description',                # 29
    'Contract Type',                     # 30 (mapped from interest_type)
    
    # Columns 31-40: Pricing values
    'Interest Type',                     # 31
    'Fair Value + Accrued Interest',     # 32
    'Accrued Interest',                  # 33
    'Fair Value',                        # 34
    'Price including Accrued',           # 35
    'Accrued Interest',                  # 36  # Note: Different from col 33
    'Price',                            # 37
    'Benchmark Yield | Index Rate',      # 38
    'Becnhmark',                        # 39  # Note: Intentional typo 'Becnhmark'
    'WAL (yrs)',                        # 40
    
    # Columns 41-50: Duration and ranges
    'Modified Duration (yrs)',           # 41
    'Convexity',                        # 42
    'Maturity',                         # 43
    'Lower Fair Value Range - Price',    # 44
    'Upper Fair Value Range - Price',    # 45
    'Lower Fair Value Range - FV',       # 46
    'Upper  Fair Value Range - FV',      # 47  # Note: Double space after 'Upper'
    'Lower Fair Value Range - MEY',      # 48
    'Upper Fair Value Range - MEY',      # 49
    'Loan Origination Date',            # 50
    
    # Columns 51-60: Dates and extensions
    'Original Maturity Date',           # 51
    'Extension 1st',                     # 52
    'Extension 2nd',                     # 53
    'Extension 3rd',                     # 54
    'Default Scenario',                  # 55
    'Conponent Yield',                  # 56  # Note: Intentional typo 'Conponent'
    'Δ Price',                          # 57
    'Δ Price due to Yield CBE',        # 58
    'Δ Price due to Credit Spread / DM', # 59
    'Δ Price due to Benchmark',         # 60
    
    # Columns 61-70: Price changes and spreads
    'Δ Price due to Yield Curve Shift', # 61
    'Δ Price due to Yield Curve Roll',  # 62
    'Δ Price due to Accretion to Par or Amortization of Premium', # 63
    'Δ Credit Spread',                  # 64
    'Δ Benchmark Yld',                  # 65
    'Δ CBE Yield',                      # 66
    'Yield Curve Shift',                 # 67
    'Yield Curve Roll',                  # 68
    'Prior Scenario',                    # 69
    'CS',                                # 70
    
    # Columns 71-80: Additional metrics
    'MY',                                # 71
    'MS',                                # 72
    'Amortization Type',                 # 73
    'Property Location',                 # 74
    'DSCR',                             # 75
    'LTV',                              # 76
    'Current Balance Prior',             # 77
    'Price Prior',                       # 78
    'Benchmark Yield Prior',             # 79
    'Credit Spread Prior',               # 80
    
    # Columns 81-87: Prior period comparisons
    'Market Yield Prior',                # 81
    'DSCR Prior',                       # 82
    'LTV Prior',                        # 83
    'WAL Prior',                        # 84
    'Duration Prior',                    # 85
    'Loan Status Prior',                 # 86
    'New Loan to Portfolio?'             # 87
]

# Quick reference for finding columns by position range
COLUMN_RANGES = {
    'core_identifiers': (1, 10),
    'loan_details': (11, 20),
    'structure': (21, 30),
    'pricing': (31, 40),
    'duration_ranges': (41, 50),
    'dates_extensions': (51, 60),
    'price_changes': (61, 70),
    'additional_metrics': (71, 80),
    'prior_period': (81, 87)
}

# Validate we have exactly 87 columns
assert len(AUDIT_COLUMN_ORDER) == 87, f"Expected 87 columns, found {len(AUDIT_COLUMN_ORDER)}"
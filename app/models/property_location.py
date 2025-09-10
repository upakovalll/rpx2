"""
Property Location model - Legacy compatibility layer.
This module provides backwards compatibility by re-exporting LoanProperty as PropertyLocation.
"""

from app.models.loan_property import LoanProperty

# For backwards compatibility
PropertyLocation = LoanProperty
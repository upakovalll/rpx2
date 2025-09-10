"""Database models."""

from .loan import Loan
from .loan_property import LoanProperty
from .property_location import PropertyLocation

__all__ = ["Loan", "LoanProperty", "PropertyLocation"]
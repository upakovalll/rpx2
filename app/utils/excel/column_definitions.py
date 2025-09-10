"""
Excel column definitions for the 87-column audit format.
This module now serves as a facade, importing from specialized sub-modules.

The definitions are split into smaller, focused files:
- definitions/column_mappings.py: Database to Excel field mappings
- definitions/column_order.py: The exact 87-column sequence
- definitions/column_groups.py: Logical groupings of columns
- definitions/column_types.py: Data type classifications
- definitions/column_transformations.py: Special mapping logic
- definitions/column_utils.py: Utility functions
"""

# Import everything from the specialized modules
from .definitions import (
    # Core mappings and order
    COLUMN_MAPPING,
    AUDIT_COLUMN_ORDER,
    COLUMN_GROUPS,
    
    # Data type classifications
    NUMERIC_COLUMNS,
    PERCENTAGE_COLUMNS,
    BASIS_POINTS_COLUMNS,
    DATE_COLUMNS,
    INTEGER_COLUMNS,
    CURRENCY_COLUMNS,
    
    # Transformations
    COLUMN_TRANSFORMATIONS,
    
    # Utility functions
    get_column_by_position,
    get_column_position,
    get_db_field_for_column,
    validate_column_count
)

# Re-export for backward compatibility
def get_column_groups():
    """Return column groups for easier management."""
    return COLUMN_GROUPS

# All exports
__all__ = [
    'COLUMN_MAPPING',
    'AUDIT_COLUMN_ORDER',
    'COLUMN_GROUPS',
    'NUMERIC_COLUMNS',
    'PERCENTAGE_COLUMNS',
    'BASIS_POINTS_COLUMNS',
    'DATE_COLUMNS',
    'INTEGER_COLUMNS',
    'CURRENCY_COLUMNS',
    'COLUMN_TRANSFORMATIONS',
    'get_column_by_position',
    'get_column_position',
    'get_db_field_for_column',
    'validate_column_count',
    'get_column_groups'
]
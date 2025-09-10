"""
Utility functions for working with Excel columns.
"""

from typing import Optional, Tuple
from .column_order import AUDIT_COLUMN_ORDER
from .column_mappings import COLUMN_MAPPING


def get_column_by_position(position: int) -> Optional[str]:
    """
    Get column name by its position (1-based) in the 87-column format.
    
    Args:
        position: Column position (1-87)
        
    Returns:
        Column name or None if position is invalid
        
    Example:
        >>> get_column_by_position(1)
        'Loan ID'
        >>> get_column_by_position(45)
        'Upper Fair Value Range - Price'
    """
    if 1 <= position <= 87:
        return AUDIT_COLUMN_ORDER[position - 1]
    return None


def get_column_position(column_name: str) -> Optional[int]:
    """
    Get position (1-based) of a column in the 87-column format.
    
    Args:
        column_name: Name of the Excel column
        
    Returns:
        Position (1-87) or None if column not found
        
    Example:
        >>> get_column_position('Loan ID')
        1
        >>> get_column_position('LTV')
        76
    """
    try:
        return AUDIT_COLUMN_ORDER.index(column_name) + 1
    except ValueError:
        return None


def get_db_field_for_column(excel_column: str) -> Optional[str]:
    """
    Get database field name for an Excel column name.
    
    Args:
        excel_column: Excel column name
        
    Returns:
        Database field name or None if no mapping exists
        
    Example:
        >>> get_db_field_for_column('Loan ID')
        'loan_id'
        >>> get_db_field_for_column('Fair Value')
        'fair_value_clean'
    """
    # Reverse lookup in COLUMN_MAPPING
    for db_field, excel_name in COLUMN_MAPPING.items():
        if excel_name == excel_column:
            return db_field
    return None


def validate_column_count() -> Tuple[bool, str]:
    """
    Validate that we have exactly 87 columns defined.
    
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        >>> validate_column_count()
        (True, '✓ Exactly 87 columns defined')
    """
    count = len(AUDIT_COLUMN_ORDER)
    if count == 87:
        return True, f"✓ Exactly {count} columns defined"
    else:
        return False, f"✗ Expected 87 columns, found {count}"


def find_columns_with_text(search_text: str) -> list:
    """
    Find all columns containing specific text (case-insensitive).
    
    Args:
        search_text: Text to search for in column names
        
    Returns:
        List of tuples (position, column_name) for matching columns
        
    Example:
        >>> find_columns_with_text('prior')
        [(77, 'Current Balance Prior'), (78, 'Price Prior'), ...]
    """
    search_lower = search_text.lower()
    results = []
    for i, col in enumerate(AUDIT_COLUMN_ORDER, 1):
        if search_lower in col.lower():
            results.append((i, col))
    return results


def get_column_range(start_pos: int, end_pos: int) -> list:
    """
    Get columns in a specific position range.
    
    Args:
        start_pos: Starting position (1-based, inclusive)
        end_pos: Ending position (1-based, inclusive)
        
    Returns:
        List of column names in the range
        
    Example:
        >>> get_column_range(1, 5)
        ['Loan ID', 'Pricing Scenario', 'Maturity Assumption', 'Credit Spread (bps)', 'Market Yield']
    """
    if start_pos < 1:
        start_pos = 1
    if end_pos > 87:
        end_pos = 87
    
    return AUDIT_COLUMN_ORDER[start_pos-1:end_pos]


def get_missing_db_mappings() -> list:
    """
    Find Excel columns that don't have database field mappings.
    
    Returns:
        List of Excel column names without database mappings
    """
    mapped_columns = set(COLUMN_MAPPING.values())
    all_columns = set(AUDIT_COLUMN_ORDER)
    return list(all_columns - mapped_columns)


def get_unmapped_db_fields(available_fields: list) -> list:
    """
    Find database fields that aren't mapped to Excel columns.
    
    Args:
        available_fields: List of available database field names
        
    Returns:
        List of database fields not in COLUMN_MAPPING
    """
    mapped_fields = set(COLUMN_MAPPING.keys())
    available_set = set(available_fields)
    return list(available_set - mapped_fields)
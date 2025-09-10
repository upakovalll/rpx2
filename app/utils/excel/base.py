"""
Base Excel writer class for managing Excel file creation.
"""

import pandas as pd
from io import BytesIO
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .formatters import ExcelFormatter

logger = logging.getLogger(__name__)


class ExcelSheet:
    """Represents a single Excel sheet with its data and formatting."""
    
    def __init__(self, name: str, data: pd.DataFrame, formatter: Optional[callable] = None):
        """
        Initialize an Excel sheet.
        
        Args:
            name: Sheet name
            data: DataFrame containing sheet data
            formatter: Optional formatting function to apply
        """
        self.name = name
        self.data = data
        self.formatter = formatter
    
    def write_to_excel(self, writer: pd.ExcelWriter) -> None:
        """
        Write this sheet to an Excel file.
        
        Args:
            writer: pandas ExcelWriter object
        """
        # Check if columns have position suffixes (for 87-column audit format)
        has_position_suffixes = any('__pos' in str(col) for col in self.data.columns)
        
        if has_position_suffixes:
            # Create a copy of the data for writing
            write_data = self.data.copy()
            
            # Extract original column names (removing __posXX suffix)
            original_columns = []
            for col in self.data.columns:
                if '__pos' in str(col):
                    original_name = str(col).rsplit('__pos', 1)[0]
                    original_columns.append(original_name)
                else:
                    original_columns.append(col)
            
            # Rename columns to remove position suffixes
            write_data.columns = original_columns
            
            # Write data to sheet with original column names
            write_data.to_excel(writer, sheet_name=self.name, index=False)
        else:
            # Write data to sheet normally
            self.data.to_excel(writer, sheet_name=self.name, index=False)
        
        # Apply formatting if provided
        if self.formatter and self.name in writer.sheets:
            worksheet = writer.sheets[self.name]
            if callable(self.formatter):
                # Pass the data with original columns for formatting
                if has_position_suffixes:
                    self.formatter(worksheet, write_data)
                else:
                    self.formatter(worksheet, self.data)
            else:
                if has_position_suffixes:
                    ExcelFormatter.format_worksheet(worksheet, write_data)
                else:
                    ExcelFormatter.format_worksheet(worksheet, self.data)


class ExcelWriter:
    """Main Excel writer that manages multiple sheets and creates the final file."""
    
    def __init__(self):
        """Initialize the Excel writer."""
        self.sheets: List[ExcelSheet] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_sheet(self, sheet: ExcelSheet) -> 'ExcelWriter':
        """
        Add a sheet to the Excel file.
        
        Args:
            sheet: ExcelSheet object to add
            
        Returns:
            Self for method chaining
        """
        self.sheets.append(sheet)
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'ExcelWriter':
        """
        Add metadata for the Excel file.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Self for method chaining
        """
        self.metadata[key] = value
        return self
    
    def create_metadata_sheet(self) -> Optional[ExcelSheet]:
        """
        Create a metadata sheet if metadata exists.
        
        Returns:
            ExcelSheet with metadata or None
        """
        if not self.metadata:
            return None
        
        # Add default metadata
        self.metadata.setdefault('Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.metadata.setdefault('Report', 'RPX Portfolio Analysis')
        
        # Convert to DataFrame
        metadata_items = [{'Field': k, 'Value': v} for k, v in self.metadata.items()]
        metadata_df = pd.DataFrame(metadata_items)
        
        return ExcelSheet('Report Info', metadata_df)
    
    def to_bytes(self) -> BytesIO:
        """
        Generate the Excel file as bytes.
        
        Returns:
            BytesIO object containing the Excel file
        """
        # Check if any sheets use the audit format (have position suffixes)
        has_audit_sheets = any(
            any('__pos' in str(col) for col in sheet.data.columns) 
            for sheet in self.sheets
        )
        
        if has_audit_sheets:
            # Use direct writer for audit format sheets
            from .writers import DirectExcelWriter
            from openpyxl import Workbook
            
            wb = Workbook()
            # Remove default sheet
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])
            
            # Add metadata sheet if exists
            metadata_sheet = self.create_metadata_sheet()
            if metadata_sheet:
                DirectExcelWriter.write_standard_sheet(
                    wb, metadata_sheet.name, metadata_sheet.data
                )
            
            # Write all sheets
            for sheet in self.sheets:
                try:
                    # Check if this is an audit format sheet
                    if any('__pos' in str(col) for col in sheet.data.columns):
                        DirectExcelWriter.write_audit_format_sheet(
                            wb, sheet.name, sheet.data
                        )
                    else:
                        DirectExcelWriter.write_standard_sheet(
                            wb, sheet.name, sheet.data
                        )
                except Exception as e:
                    logger.error(f"Error writing sheet {sheet.name}: {str(e)}")
                    raise
            
            # Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            return output
        else:
            # Use standard pandas writer for regular sheets
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Add metadata sheet if exists
                metadata_sheet = self.create_metadata_sheet()
                if metadata_sheet:
                    metadata_sheet.write_to_excel(writer)
                
                # Write all sheets
                for sheet in self.sheets:
                    try:
                        sheet.write_to_excel(writer)
                    except Exception as e:
                        logger.error(f"Error writing sheet {sheet.name}: {str(e)}")
                        raise
            
            output.seek(0)
            return output
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the Excel file to disk.
        
        Args:
            filepath: Path where to save the file
        """
        excel_bytes = self.to_bytes()
        with open(filepath, 'wb') as f:
            f.write(excel_bytes.read())


class ExcelBuilder:
    """Builder pattern for constructing Excel files."""
    
    def __init__(self):
        """Initialize the builder."""
        self.writer = ExcelWriter()
    
    def with_loans_data(self, loans_data: List[Dict[str, Any]]) -> 'ExcelBuilder':
        """
        Add loans sheet to the Excel file.
        
        Args:
            loans_data: List of loan records
            
        Returns:
            Self for method chaining
        """
        if loans_data:
            from .sheets.pricing_sheet import PricingSheet
            sheet = PricingSheet.create_from_loans(loans_data)
            self.writer.add_sheet(sheet)
        return self
    
    def with_properties_data(self, properties_data: List[Dict[str, Any]]) -> 'ExcelBuilder':
        """
        Add properties sheet to the Excel file.
        
        Args:
            properties_data: List of property records
            
        Returns:
            Self for method chaining
        """
        if properties_data:
            df = pd.DataFrame(properties_data)
            df = ExcelFormatter.convert_dataframe_types(df)
            sheet = ExcelSheet('Properties', df, ExcelFormatter.format_worksheet)
            self.writer.add_sheet(sheet)
        return self
    
    def with_pricing_data(self, pricing_data: List[Dict[str, Any]]) -> 'ExcelBuilder':
        """
        Add pricing results sheet to the Excel file.
        
        Args:
            pricing_data: List of pricing records
            
        Returns:
            Self for method chaining
        """
        if pricing_data:
            from .sheets.pricing_sheet import PricingSheet
            sheet = PricingSheet.create_from_pricing_data(pricing_data)
            self.writer.add_sheet(sheet)
        return self
    
    def with_portfolio_summary(self, summary_data: List[Dict[str, Any]]) -> 'ExcelBuilder':
        """
        Add portfolio summary sheet to the Excel file.
        
        Args:
            summary_data: Portfolio summary records
            
        Returns:
            Self for method chaining
        """
        if summary_data:
            df = pd.DataFrame(summary_data)
            df = ExcelFormatter.convert_dataframe_types(df)
            sheet = ExcelSheet('Portfolio Summary', df, ExcelFormatter.format_worksheet)
            self.writer.add_sheet(sheet)
        return self
    
    def with_risk_metrics(self, risk_data: List[Dict[str, Any]]) -> 'ExcelBuilder':
        """
        Add risk metrics sheet to the Excel file.
        
        Args:
            risk_data: Risk metrics records
            
        Returns:
            Self for method chaining
        """
        if risk_data:
            df = pd.DataFrame(risk_data)
            df = ExcelFormatter.convert_dataframe_types(df)
            sheet = ExcelSheet('Risk Metrics', df, ExcelFormatter.format_worksheet)
            self.writer.add_sheet(sheet)
        return self
    
    def with_market_data(self, benchmarks: List[Dict], spreads: List[Dict]) -> 'ExcelBuilder':
        """
        Add market data sheet to the Excel file.
        
        Args:
            benchmarks: Benchmark rates
            spreads: Credit spreads
            
        Returns:
            Self for method chaining
        """
        from .formatters import DataProcessor
        
        market_df = DataProcessor.prepare_market_data(benchmarks, spreads)
        if not market_df.empty:
            sheet = ExcelSheet('Market Data', market_df, ExcelFormatter.format_worksheet)
            self.writer.add_sheet(sheet)
        return self
    
    def with_metadata(self, **kwargs) -> 'ExcelBuilder':
        """
        Add metadata to the Excel file.
        
        Args:
            **kwargs: Metadata key-value pairs
            
        Returns:
            Self for method chaining
        """
        for key, value in kwargs.items():
            self.writer.add_metadata(key, value)
        return self
    
    def build(self) -> BytesIO:
        """
        Build and return the Excel file.
        
        Returns:
            BytesIO object containing the Excel file
        """
        return self.writer.to_bytes()
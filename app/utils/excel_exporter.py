"""
Excel export utilities for loan and pricing data.
Now uses modular architecture for better maintainability.
"""

import pandas as pd
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import logging

# Import from new modular structure
from .excel.base import ExcelBuilder, ExcelWriter, ExcelSheet
from .excel.formatters import ExcelFormatter, DataProcessor
from .excel.sheets.pricing_sheet import PricingSheet

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Utility class for exporting data to Excel format.
    
    This class now delegates to the modular Excel export system
    while maintaining backward compatibility.
    """
    
    @staticmethod
    def safe_value(value: Any) -> Any:
        """Convert database types to Excel-compatible values, preserving data types.
        
        Delegates to ExcelFormatter.safe_value for consistency.
        """
        return ExcelFormatter.safe_value(value)
    
    @staticmethod
    def create_loans_excel(loans_data: List[Dict[str, Any]], properties_data: Optional[List[Dict[str, Any]]] = None) -> BytesIO:
        """
        Create Excel file with loans data.
        
        Args:
            loans_data: List of loan records from materialized view
            properties_data: Optional list of property records
            
        Returns:
            BytesIO object containing Excel file
        """
        # Use the new ExcelBuilder for cleaner code
        builder = ExcelBuilder()
        builder.with_loans_data(loans_data)
        
        if properties_data:
            builder.with_properties_data(properties_data)
        
        return builder.build()
    
    @staticmethod
    def create_pricing_results_excel(
        pricing_data: List[Dict[str, Any]],
        summary_data: Optional[List[Dict[str, Any]]] = None,
        risk_metrics: Optional[List[Dict[str, Any]]] = None,
        benchmarks: Optional[List[Dict[str, Any]]] = None,
        spreads: Optional[List[Dict[str, Any]]] = None
    ) -> BytesIO:
        """
        Create Excel file with pricing results and analysis.
        
        Args:
            pricing_data: Pricing results from database
            summary_data: Portfolio summary data
            risk_metrics: Risk metrics data
            benchmarks: Current benchmark rates
            spreads: Current credit spreads
            
        Returns:
            BytesIO object containing Excel file
        """
        # Use the new ExcelBuilder for cleaner code
        builder = ExcelBuilder()
        
        if pricing_data:
            builder.with_pricing_data(pricing_data)
        
        if summary_data:
            builder.with_portfolio_summary(summary_data)
        
        if risk_metrics:
            builder.with_risk_metrics(risk_metrics)
        
        if benchmarks or spreads:
            builder.with_market_data(benchmarks or [], spreads or [])
        
        return builder.build()
    
    @staticmethod
    def create_portfolio_analysis_excel(
        portfolio_summary: List[Dict[str, Any]],
        individual_loans: Optional[List[Dict[str, Any]]] = None,
        breakdowns: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> BytesIO:
        """
        Create comprehensive portfolio analysis Excel report.
        
        Args:
            portfolio_summary: Overall portfolio metrics
            individual_loans: Individual loan data
            breakdowns: Dictionary with breakdown analyses by category
            
        Returns:
            BytesIO object containing Excel file
        """
        # Use the new modular system
        writer = ExcelWriter()
        
        # Add portfolio summary
        if portfolio_summary:
            summary_df = pd.DataFrame(portfolio_summary)
            summary_df = ExcelFormatter.convert_dataframe_types(summary_df)
            writer.add_sheet(ExcelSheet('Portfolio Summary', summary_df, ExcelFormatter.format_worksheet))
        
        # Add individual loans
        if individual_loans:
            loans_sheet = PricingSheet.create_from_pricing_data(individual_loans)
            loans_sheet.name = 'Individual Loans'  # Rename for this context
            writer.add_sheet(loans_sheet)
        
        # Add breakdown sheets
        if breakdowns:
            for breakdown_type, breakdown_data in breakdowns.items():
                if breakdown_data:
                    breakdown_df = pd.DataFrame(breakdown_data)
                    breakdown_df = ExcelFormatter.convert_dataframe_types(breakdown_df)
                    sheet_name = breakdown_type.replace('_', ' ').title() + ' Analysis'
                    writer.add_sheet(ExcelSheet(sheet_name, breakdown_df, ExcelFormatter.format_worksheet))
        
        return writer.to_bytes()
    
    @staticmethod
    def create_complete_report_excel(
        loans_data: List[Dict[str, Any]],
        properties_data: List[Dict[str, Any]],
        pricing_data: List[Dict[str, Any]],
        summary_data: List[Dict[str, Any]],
        risk_metrics: List[Dict[str, Any]],
        benchmarks: List[Dict[str, Any]],
        spreads: List[Dict[str, Any]]
    ) -> BytesIO:
        """
        Create comprehensive Excel report with all data.
        
        Returns:
            BytesIO object containing Excel file
        """
        # Use the new ExcelBuilder with metadata
        builder = ExcelBuilder()
        
        # Add metadata
        builder.with_metadata(
            Report='RPX Loan Portfolio Analysis',
            Generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            Total_Loans=len(loans_data) if loans_data else 0,
            Total_Properties=len(properties_data) if properties_data else 0,
            Analysis_Date=date.today().strftime('%Y-%m-%d')
        )
        
        # Add source data sheets
        if loans_data:
            loans_df = pd.DataFrame(loans_data)
            loans_df = ExcelFormatter.convert_dataframe_types(loans_df)
            builder.writer.add_sheet(ExcelSheet('Source Loans', loans_df, ExcelFormatter.format_worksheet))
        
        if properties_data:
            builder.with_properties_data(properties_data)
        
        # Add analysis sheets
        if pricing_data:
            builder.with_pricing_data(pricing_data)
        
        if summary_data:
            builder.with_portfolio_summary(summary_data)
        
        if risk_metrics:
            builder.with_risk_metrics(risk_metrics)
        
        if benchmarks or spreads:
            builder.with_market_data(benchmarks or [], spreads or [])
        
        return builder.build()
    
    @staticmethod
    def _format_worksheet(worksheet, dataframe):
        """Apply formatting to worksheet.
        
        Delegates to ExcelFormatter.format_worksheet for consistency.
        """
        ExcelFormatter.format_worksheet(worksheet, dataframe)
    
    @staticmethod
    def _format_pricing_data(pricing_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Format pricing data from mv_pricing_engine_output_complete_v4_layered with proper data types.
        
        This method now delegates to PricingSheet for the actual formatting.
        """
        if not pricing_data:
            return pd.DataFrame()
        
        # Delegate to the PricingSheet module
        return PricingSheet._format_pricing_data(pricing_data)
    

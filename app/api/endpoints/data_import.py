"""
Data Import API endpoints for uploading benchmark and loan data from Excel files.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, date
import io
import re
from collections import defaultdict
from typing import List, Dict, Any, Optional

from app.database.session import get_db

router = APIRouter()


# Term conversion mapping from Excel labels to years (from import_benchmark_data.py)
TERM_MAPPING = {
    '1 Mo': 0.0833,
    '1.5 Mo': 0.125,
    '2 Mo': 0.1667,
    '3 Mo': 0.25,
    '4 Mo': 0.3333,
    '6 Mo': 0.5,
    '1 Yr': 1.0,
    '2 Yr': 2.0,
    '3 Yr': 3.0,
    '5 Yr': 5.0,
    '7 Yr': 7.0,
    '10 Yr': 10.0,
    '20 Yr': 20.0,
    '30 Yr': 30.0
}

# Benchmark type constants
BENCHMARK_TYPES = {
    'UST': 'UST',
    'SOFR_SWAP': 'SOFR_SWAP',
    'SOFR1M': 'SOFR1M',
    'SOFR3M': 'SOFR3M', 
    'SOFR6M': 'SOFR6M',
    'EURIBOR1M': 'EURIBOR1M',
    'EURIBOR3M': 'EURIBOR3M',
    'EURIBOR6M': 'EURIBOR6M',
    'SONIA1M': 'SONIA1M',
    'SONIA3M': 'SONIA3M',
    'GBPLIBOR1M': 'GBPLIBOR1M',
    'GBPLIBOR3M': 'GBPLIBOR3M',
    'PRIME': 'PRIME',
    'AUSBBSW': 'AUSBBSW',
    'CADDOR': 'CADDOR'
}


def parse_excel_rate(val):
    """Parse rate from Excel (convert to decimal if needed)."""
    if pd.isna(val) or val == '' or val == '-':
        return None
    try:
        rate = Decimal(str(val))
        # If rate is > 1, assume it's in percentage format, convert to decimal
        if rate > 1:
            rate = rate / 100
        return float(rate)  # Return as float for JSON serialization
    except:
        return None


def parse_excel_date(val):
    """Parse date from Excel."""
    if pd.isna(val) or val == '' or val == 'R':
        return None
    
    # If it's already a datetime object from pandas
    if isinstance(val, pd.Timestamp):
        return val.date()
    elif isinstance(val, datetime):
        return val.date()
    elif isinstance(val, date):
        return val
    
    # If it's a string, try to parse it
    if isinstance(val, str):
        try:
            # Try DD.MM.YY format
            if '.' in val:
                parts = val.split('.')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year_int = int(year)
                        # Use 2000s for 00-50, 1900s for 51-99
                        if year_int <= 50:
                            year = '20' + year
                        else:
                            year = '19' + year
                    return datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y").date()
            return pd.to_datetime(val).date()
        except:
            pass
    
    return None


def parse_excel_percentage(val):
    """Parse percentage from Excel (already in decimal format)."""
    if pd.isna(val) or val == '' or val == '-':
        return None
    try:
        # Excel stores percentages as decimals (5.75% = 0.0575)
        return float(Decimal(str(val)))
    except:
        return None


def parse_excel_number(val):
    """Parse number from Excel."""
    if pd.isna(val) or val == '' or val == '-' or val == ' -   ':
        return None
    try:
        # Remove any formatting characters
        if isinstance(val, str):
            val = val.replace(',', '').replace(' ', '')
        return float(Decimal(str(val)))
    except:
        return None


def calculate_term_from_accrual_date(accrual_date, reference_date):
    """Calculate term in years from accrual date."""
    if pd.isna(accrual_date) or pd.isna(reference_date):
        return None
    
    try:
        if isinstance(accrual_date, str):
            accrual_date = pd.to_datetime(accrual_date)
        if isinstance(reference_date, str):
            reference_date = pd.to_datetime(reference_date)
            
        days_diff = (accrual_date - reference_date).days
        return round(days_diff / 365.25, 4)  # Convert to years
    except:
        return None


@router.post("/benchmark-rates", operation_id="import_benchmark_rates")
async def import_benchmark_rates(
    file: UploadFile = File(..., description="Excel file containing benchmark rates"),
    clear_existing: bool = True,
    db: Session = Depends(get_db)
):
    """Import benchmark rates from an Excel file (DISTILLED_BENCHMARK_YIELD.xlsx format)."""
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        # Read Excel file into memory
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
        
        all_records = []
        
        # Extract US Treasury data (columns O-AC)
        treasury_records = extract_us_treasury_data(df)
        all_records.extend(treasury_records)
        
        # Extract SOFR data (columns BU-CH)
        sofr_records = extract_sofr_data(df)
        all_records.extend(sofr_records)
        
        # Extract European indices (columns CT-DG)
        european_records = extract_european_data(df)
        all_records.extend(european_records)
        
        # Extract UK indices (columns CJ-DQ)
        uk_records = extract_uk_data(df)
        all_records.extend(uk_records)
        
        # Extract other indices
        other_records = extract_other_indices_data(df)
        all_records.extend(other_records)
        
        if not all_records:
            raise HTTPException(status_code=400, detail="No valid benchmark data found in the file")
        
        # Clear existing data if requested
        if clear_existing:
            db.execute(text("DELETE FROM market_benchmarks"))
        
        # Insert records in batches
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i + batch_size]
            
            # Insert batch using raw SQL for better performance
            for record in batch:
                db.execute(text("""
                    INSERT INTO market_benchmarks 
                    (benchmark_date, benchmark_type, term_years, rate, currency, source)
                    VALUES (:benchmark_date, :benchmark_type, :term_years, :rate, :currency, :source)
                    ON CONFLICT (benchmark_date, benchmark_type, currency, term_years) 
                    DO UPDATE SET 
                        rate = EXCLUDED.rate,
                        source = EXCLUDED.source,
                        created_at = CURRENT_TIMESTAMP
                """), record)
            
            total_inserted += len(batch)
        
        db.commit()
        
        # Get summary statistics
        summary = db.execute(text("""
            SELECT benchmark_type, COUNT(*) as count, 
                   MIN(benchmark_date) as min_date, 
                   MAX(benchmark_date) as max_date
            FROM market_benchmarks
            GROUP BY benchmark_type
            ORDER BY benchmark_type
        """)).fetchall()
        
        return {
            "message": f"Successfully imported {total_inserted} benchmark records",
            "summary": [
                {
                    "benchmark_type": row[0],
                    "count": row[1],
                    "date_range": f"{row[2]} to {row[3]}"
                }
                for row in summary
            ]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@router.post("/loans", operation_id="import_loans")
async def import_loans(
    file: UploadFile = File(..., description="Excel file containing loan data"),
    clear_existing: bool = True,
    db: Session = Depends(get_db)
):
    """Import loans from an Excel file (DISTILLED_EXCEL.xlsx format)."""
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        # Read Excel file into memory
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
        
        # Process loans
        loans, properties = process_loan_data(df)
        
        if not loans:
            raise HTTPException(status_code=400, detail="No valid loan data found in the file")
        
        # Clear existing data if requested
        if clear_existing:
            # Delete in correct order due to foreign keys
            db.execute(text("DELETE FROM loan_properties"))
            db.execute(text("DELETE FROM loans"))
        
        # Insert loans
        inserted_loans = 0
        for loan in loans:
            # Convert any remaining Decimal/numpy types to Python types
            clean_loan = {}
            for k, v in loan.items():
                if isinstance(v, Decimal):
                    clean_loan[k] = float(v)
                elif isinstance(v, (np.integer, np.floating)):
                    clean_loan[k] = float(v)
                elif isinstance(v, (date, datetime)):
                    clean_loan[k] = v.isoformat() if v else None
                else:
                    clean_loan[k] = v
            
            # Build INSERT query dynamically based on non-null fields
            fields = [k for k, v in clean_loan.items() if v is not None]
            placeholders = [f":{field}" for field in fields]
            
            if fields:
                query = f"""
                    INSERT INTO loans ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                """
                db.execute(text(query), clean_loan)
                inserted_loans += 1
        
        # Insert properties
        inserted_properties = 0
        for prop in properties:
            db.execute(text("""
                INSERT INTO loan_properties 
                (rp_system_id, property_number, street, city, state, zip_code, country, region)
                VALUES (:rp_system_id, :property_number, :street, :city, :state, :zip_code, :country, :region)
            """), prop)
            inserted_properties += 1
        
        db.commit()
        
        # Get summary statistics
        loan_count = db.execute(text("SELECT COUNT(*) FROM loans")).scalar()
        property_count = db.execute(text("SELECT COUNT(*) FROM loan_properties")).scalar()
        
        return {
            "message": f"Successfully imported {inserted_loans} loans and {inserted_properties} properties",
            "summary": {
                "total_loans": loan_count,
                "total_properties": property_count,
                "loans_imported": inserted_loans,
                "properties_imported": inserted_properties
            }
        }
        
    except SQLAlchemyError as e:
        db.rollback()
        # Extract more specific error message
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(status_code=400, detail=f"Database error: {error_msg}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


# Helper functions for extracting benchmark data

def extract_us_treasury_data(df) -> List[Dict]:
    """Extract US Treasury daily rates (columns O-AC)."""
    records = []
    
    # Date column is O (14), term columns are P-AC (15-28)
    date_col = 14
    rate_cols = list(range(15, 29))  # P through AC
    
    # Get term mappings from row 4 (header row)
    if len(df) > 4:
        term_row = df.iloc[4]
        col_to_term = {}
        
        for col_idx in rate_cols:
            if col_idx < len(term_row):
                term_label = str(term_row.iloc[col_idx]).strip()
                if term_label in TERM_MAPPING:
                    col_to_term[col_idx] = TERM_MAPPING[term_label]
                else:
                    # Try to parse numeric term directly
                    try:
                        if 'Mo' in term_label:
                            months = float(re.findall(r'[\d.]+', term_label)[0])
                            col_to_term[col_idx] = round(months / 12, 4)
                        elif 'Yr' in term_label:
                            years = float(re.findall(r'[\d.]+', term_label)[0])
                            col_to_term[col_idx] = years
                    except:
                        pass
        
        # Process data rows (starting from row 5)
        for row_idx in range(5, len(df)):
            row = df.iloc[row_idx]
            
            # Get date from column O
            if date_col < len(row):
                benchmark_date = parse_excel_date(row.iloc[date_col])
                if benchmark_date:
                    # Extract rates for each term
                    for col_idx, term_years in col_to_term.items():
                        if col_idx < len(row):
                            rate = parse_excel_rate(row.iloc[col_idx])
                            if rate is not None:
                                records.append({
                                    'benchmark_date': benchmark_date,
                                    'benchmark_type': BENCHMARK_TYPES['UST'],
                                    'term_years': term_years,
                                    'rate': rate,
                                    'currency': 'USD',
                                    'source': 'US Treasury'
                                })
    
    return records


def extract_sofr_data(df) -> List[Dict]:
    """Extract SOFR forward curves (columns BU-CH)."""
    records = []
    
    # SOFR sections
    sofr_sections = [
        ('SOFR1M', 72),  # Column BU
        ('SOFR3M', 77),  # Column BZ
        ('SOFR6M', 82)   # Column CE
    ]
    
    for sofr_type, col_idx in sofr_sections:
        records.extend(extract_forward_curve(df, sofr_type, col_idx, 'USD', 'FRED/Bloomberg'))
    
    return records


def extract_european_data(df) -> List[Dict]:
    """Extract European indices (EURIBOR columns CT-DG)."""
    records = []
    
    # EURIBOR sections
    euribor_sections = [
        ('EURIBOR1M', 97),   # Column CT
        ('EURIBOR3M', 102),  # Column CY
        ('EURIBOR6M', 107)   # Column DD
    ]
    
    for euribor_type, col_idx in euribor_sections:
        records.extend(extract_forward_curve(df, euribor_type, col_idx, 'EUR', 'Bloomberg'))
    
    return records


def extract_uk_data(df) -> List[Dict]:
    """Extract UK indices (SONIA/LIBOR columns CJ-DQ)."""
    records = []
    
    # UK sections
    uk_sections = [
        ('SONIA1M', 87),      # Column CJ
        ('SONIA3M', 92),      # Column CO
        ('GBPLIBOR1M', 112),  # Column DI
        ('GBPLIBOR3M', 117)   # Column DN
    ]
    
    for uk_type, col_idx in uk_sections:
        records.extend(extract_forward_curve(df, uk_type, col_idx, 'GBP', 'Bloomberg'))
    
    return records


def extract_other_indices_data(df) -> List[Dict]:
    """Extract other indices (Australian, Canadian, Prime)."""
    records = []
    
    # Other sections with their Excel identifiers
    other_sections = [
        ('AUSBBSW', 122, 'AUD', 'Bloomberg', 'AUSB'),
        ('CADDOR', 127, 'CAD', 'Bloomberg', 'CAD DOR 3M'),
        ('PRIME', 152, 'USD', 'Bloomberg', 'Prime Rate')
    ]
    
    for index_type, col_idx, currency, source, identifier in other_sections:
        records.extend(extract_forward_curve(df, index_type, col_idx, currency, source, identifier))
    
    return records


def extract_forward_curve(df, curve_type, col_idx, currency, source, identifier=None) -> List[Dict]:
    """Extract forward curve data from a specific column."""
    records = []
    
    if col_idx >= len(df.columns):
        return records
    
    # Use custom identifier if provided, otherwise use curve_type
    search_string = identifier if identifier else curve_type
    
    # Find the row with the curve type identifier
    benchmark_date = None
    data_start_row = None
    
    for row_idx in range(min(10, len(df))):
        if row_idx < len(df) and col_idx < len(df.columns):
            cell_val = str(df.iloc[row_idx, col_idx])
            if search_string in cell_val:
                # Date should be in the next row
                if row_idx + 1 < len(df):
                    benchmark_date = parse_excel_date(df.iloc[row_idx + 1, col_idx])
                    data_start_row = row_idx + 2
                break
    
    if not benchmark_date or data_start_row is None:
        return records
    
    # Get accrual dates from column BO (66) to calculate terms
    accrual_dates_col = 66
    
    # Extract forward curve data
    max_rows = min(625, len(df) - data_start_row)
    for i in range(max_rows):
        row_idx = data_start_row + i
        if row_idx >= len(df):
            break
            
        # Get rate
        rate = parse_excel_rate(df.iloc[row_idx, col_idx])
        if rate is None:
            continue
        
        # Calculate term
        term_years = None
        if accrual_dates_col < len(df.columns):
            accrual_date = parse_excel_date(df.iloc[row_idx, accrual_dates_col])
            if accrual_date:
                term_years = calculate_term_from_accrual_date(accrual_date, benchmark_date)
        
        # Fallback: use row position
        if term_years is None or term_years <= 0:
            term_years = round(i / 12, 4)  # Monthly periods
        
        if term_years > 0:
            records.append({
                'benchmark_date': benchmark_date,
                'benchmark_type': BENCHMARK_TYPES.get(curve_type, curve_type),
                'term_years': term_years,
                'rate': rate,
                'currency': currency,
                'source': source
            })
    
    return records


# Helper functions for processing loan data

def process_loan_data(df) -> tuple[List[Dict], List[Dict]]:
    """Process loan data from Excel DataFrame."""
    
    # Column mapping from Excel to database
    COLUMN_MAPPING = {
        'System ID': 'rp_system_id',
        'Pricing Scenario': 'pricing_scenario',
        'Maturity Assumption': 'maturity_assumption',
        'Credit Spread': 'credit_spread',
        'Market Yield (or Discount Rate)': 'market_yield',
        'Loss Scenario': 'loss_scenario',
        'PD': 'pd',
        'EAD': 'ead',
        'LGD': 'lgd',
        'Lag to Recovery': 'lag_to_recovery',
        'Default Date': 'default_date',
        'CDR': 'cdr',
        'Client Loan Number': 'client_loan_number',
        'Loan Name': 'loan_name',
        'Sector': 'property_sector',
        'Property Type': 'property_type',
        'Property Lifecycle Financing': 'property_lifecycle_financing',
        'Sponsor/Borrower': 'sponsor_borrower',
        'Current Balance - Includes Accrued Interest & PIK Interest': 'current_balance',
        'Currency': 'currency',
        'Client % of Total Loan Facility': 'client_percentage',
        'PIK Balance': 'pik_balance',
        'Position in Capital Stack': 'position_in_capital_stack',
        'Periodicity': 'periodicity',
        'Interest Day Count': 'interest_day_count',
        'Loan Status': 'loan_status',
        'Propoerty & Loan Commentary': 'commentary',
        'Contract Type': 'interest_type',
        'Becnhmark': 'floating_rate_index',
        'Maturity': 'original_maturity_date',
        'Loan Origination Date': 'origination_date',
        'Origination Date': 'origination_date',
        'First Payment Date': 'first_payment_date',
        'Original Balance | Total Committed Line': 'original_balance',
        'Original Maturity Date': 'original_maturity_date',
        'Extension 1st': 'first_extension_date',
        'Extension 2nd': 'second_extension_date',
        'Extension 3rd': 'third_extension_date',
        'Amortization Type': 'amortization_type',
        'DSCR': 'dscr_current',
        'LTV': 'ltv_current',
        'IO End Date': 'io_end_date',
        'Original Amortization Term': 'original_amortization_term',
        'Contractual P&I Payment Amount': 'contractual_pi_payment_amount',
        'Accrual Type': 'accrual_type',
        'PIK Coupon': 'pik_coupon',
        'Commitment Type': 'commitment_type',
        'Unfunded Commitment Fee': 'unfunded_commitment_fee',
        'Interest Type': 'interest_type',
        'Fixed Rate Coupon': 'fixed_rate_coupon',
        'Floating Rate Index': 'floating_rate_index',
        'Floating Rate Margin': 'floating_rate_margin',
        'Index Cap': 'index_cap',
        'Index Floor ': 'index_floor',
        'LTV - Current': 'ltv_current',
        'DSCR - Current': 'dscr_current',
        'Debt Yield - Current': 'debt_yield_current',
        'NOI': 'noi',
        'Prepayment Lockout End Date': 'prepayment_lockout_end_date',
        'Open Call Period Date': 'open_call_period_date',
        '1st Extension  Date': 'first_extension_date',
        '1st Extension Fee': 'first_extension_fee',
        '2nd Extension  Date': 'second_extension_date',
        '2nd Extension Fee': 'second_extension_fee',
        '3rd Extension  Date': 'third_extension_date',
        '3rd Extension Fee': 'third_extension_fee',
        'Exit Fee': 'exit_fee',
        'Client Internal Credit Rating, if available': 'internal_credit_rating',
        'Client Internal Watchlist Monitoring': 'watchlist_monitoring',
        'Bank Loan - Cpn Step Up Date or Hybrid fixed to Floating Date': 'step_up_date',
        'Bank Loan - Cpn Step Up (Incremental) Rate': 'step_up_incremental_rate',
        'Prepayment Penalty Type': 'prepayment_penalty_type',
        'Prepayment Penalty Description': 'prepayment_penalty_description',
        'Loan in Forbearance?': 'in_forbearance',
        'Forbearance Start Date': 'forbearance_start_date',
        'Forbearance Original  Term': 'forbearance_original_term',
        'Forbearance of P&I or P': 'forbearance_type',
        'Forbearance Payback Start Date': 'forbearance_payback_start_date',
        'Forbearance Payback Term': 'forbearance_payback_term',
        'P & P&I Scheduled Amortization': 'pi_scheduled_amortization',
        'Custom Payment Dates Schedule': 'custom_payment_dates_schedule',
        'Default Interest Schedule': 'default_interest_schedule',
        'Preferred Equity w Equity Kicker Schedule': 'preferred_equity_equity_kicker_schedule',
        'Step-Up Coupons': 'step_up_coupons',
        'Step-Up Margin or Interest Rate Floor on Floating Rate Loans': 'step_up_margin_interest_rate_floor',
        'Credit Utilization Proforma Assumptions': 'proforma_assumptions',
        'Custom Interest Type Timing: PIK Interest| PIK Interest&Pay Current': 'custom_interest_type_timing',
        'x1': 'x1',
        'x2': 'x2',
        'x3': 'x3',
    }
    
    loans = []
    all_properties = []
    
    for idx, row in df.iterrows():
        loan = {}
        
        # Process each Excel column using the mapping
        for excel_col, db_field in COLUMN_MAPPING.items():
            if excel_col in df.columns:
                value = row[excel_col]
                
                # Parse value based on database field type
                if db_field in ['rp_system_id']:
                    try:
                        loan[db_field] = int(value) if not pd.isna(value) else None
                    except:
                        loan[db_field] = None
                elif db_field in ['lag_to_recovery', 'original_amortization_term',
                                'forbearance_original_term', 'forbearance_payback_term']:
                    try:
                        loan[db_field] = int(value) if not pd.isna(value) else None
                    except:
                        loan[db_field] = None
                elif db_field in ['credit_spread', 'market_yield', 'pd', 'ead', 'lgd', 'cdr', 'client_percentage',
                                'ltv_current', 'debt_yield_current', 'pik_coupon', 'unfunded_commitment_fee',
                                'fixed_rate_coupon', 'floating_rate_margin', 'index_cap', 'index_floor',
                                'first_extension_fee', 'second_extension_fee', 'third_extension_fee', 'exit_fee',
                                'step_up_incremental_rate']:
                    loan[db_field] = parse_excel_percentage(value)
                elif db_field in ['current_balance', 'pik_balance', 'noi',
                                'contractual_pi_payment_amount', 'dscr_current', 'original_balance']:
                    loan[db_field] = parse_excel_number(value)
                elif db_field in ['origination_date', 'original_maturity_date', 'default_date',
                                'io_end_date', 'prepayment_lockout_end_date', 'open_call_period_date',
                                'first_extension_date', 'second_extension_date', 'third_extension_date',
                                'step_up_date', 'forbearance_start_date', 'forbearance_payback_start_date',
                                'first_payment_date']:
                    loan[db_field] = parse_excel_date(value)
                elif db_field in ['pi_scheduled_amortization', 'custom_payment_dates_schedule',
                                'default_interest_schedule', 'preferred_equity_equity_kicker_schedule',
                                'step_up_coupons', 'step_up_margin_interest_rate_floor',
                                'proforma_assumptions', 'custom_interest_type_timing']:
                    # JSONB fields - set to NULL for now
                    loan[db_field] = None
                else:
                    # String fields
                    loan[db_field] = str(value).strip() if not pd.isna(value) else None
            else:
                loan[db_field] = None
        
        # Handle special cases
        if not loan.get('currency'):
            loan['currency'] = 'USD'
        if loan.get('client_percentage') is None:
            loan['client_percentage'] = 100
        
        # Only add if has valid rp_system_id
        if loan.get('rp_system_id'):
            loans.append(loan)
            
            # Extract properties for this loan
            properties = extract_properties_from_row(row, loan['rp_system_id'])
            all_properties.extend(properties)
    
    return loans, all_properties


def extract_properties_from_row(row, loan_id) -> List[Dict]:
    """Extract property data from Excel row."""
    properties = []
    
    # Property field mappings
    property_mappings = [
        {
            'number': 1,
            'street': 'Property #1 Street | Indicator | CUSIP',
            'city': 'Property #1 City',
            'state': 'Property #1 State',
            'zip_code': 'Property #1 Zip Code',
            'country': 'Property #1 Country',
            'region': 'Property #1 Region'
        },
        {
            'number': 2,
            'street': 'Property #2 Street | Indicator | CUSIP',
            'city': 'Property #2 City',
            'state': 'Property #2 State',
            'zip_code': 'Property #2 Zip Code',
            'country': 'Property #2 Country',
            'region': 'Property #2 Region'
        },
        {
            'number': 3,
            'street': 'Property #3 Street | Indicator | CUSIP',
            'city': 'Property #3 City',
            'state': 'Property #3 State',
            'zip_code': 'Property #3 Zip Code',
            'country': 'Property #3 Country',
            'region': 'Property #3 Region'
        }
    ]
    
    for prop_map in property_mappings:
        # Check if property has any data
        has_data = False
        property_data = {
            'rp_system_id': loan_id,
            'property_number': prop_map['number'],
            'street': None,
            'city': None,
            'state': None,
            'zip_code': None,
            'country': 'United States',
            'region': None
        }
        
        # Extract each field
        for field, excel_col in prop_map.items():
            if field == 'number':
                continue
                
            if excel_col in row.index and not pd.isna(row[excel_col]) and str(row[excel_col]).strip():
                property_data[field] = str(row[excel_col]).strip()
                has_data = True
        
        # Only add property if it has data
        if has_data:
            properties.append(property_data)
    
    return properties
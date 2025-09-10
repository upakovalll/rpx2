"""
Loans API endpoints - Updated to match actual database schema.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from decimal import Decimal

from app.database.session import get_db
from app.models.loan import Loan
from app.models.loan_property import LoanProperty
from app.schemas.loan import (
    LoanCreate, 
    LoanUpdate, 
    LoanResponse,
    LoanDetailResponse,
    LoanIdentification,
    PropertyLocationResponse,
    PropertyDetails,
    FinancialTerms,
    RiskMetrics,
    PricingResults
)

router = APIRouter()

@router.get("/")
async def get_loans(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all loans."""
    loans = db.query(Loan).offset(skip).limit(limit).all()
    # Use jsonable_encoder to handle date serialization
    return JSONResponse(content=jsonable_encoder(loans))

@router.get("/{rp_system_id}")
async def get_loan(rp_system_id: int, db: Session = Depends(get_db)):
    """Get a specific loan by its rp_system_id."""
    loan = db.query(Loan).filter(Loan.rp_system_id == rp_system_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return JSONResponse(content=jsonable_encoder(loan))

@router.get("/by-system-id/{rp_system_id}", response_model=LoanDetailResponse, operation_id="get_loan_by_system_id")
async def get_loan_by_system_id(rp_system_id: int, db: Session = Depends(get_db)):
    """Get loan details in structured format by rp_system_id."""
    loan = db.query(Loan).filter(Loan.rp_system_id == rp_system_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Get associated properties
    properties = db.query(LoanProperty).filter(LoanProperty.rp_system_id == rp_system_id).all()
    
    # Build property locations
    property_locations = [
        PropertyLocationResponse(
            location_id=str(prop.id),  # Convert integer to string for UUID compatibility
            street=prop.street,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code,
            country=prop.country,
            region=prop.region,
            created_at=prop.created_at
        ) for prop in properties
    ]
    
    # Calculate interest rate
    interest_rate = loan.fixed_rate_coupon if loan.interest_type == 'Fixed' else loan.floating_rate_margin
    
    return LoanDetailResponse(
        loan_identification=LoanIdentification(
            rp_system_id=loan.rp_system_id,
            client_loan_number=loan.client_loan_number,
            loan_name=loan.loan_name
        ),
        property_details=PropertyDetails(
            sector=loan.property_sector,
            property_type=loan.property_type,
            locations=property_locations
        ),
        financial_terms=FinancialTerms(
            original_balance=loan.original_balance,
            current_balance=loan.current_balance,
            interest_rate=interest_rate,
            maturity_date=str(loan.original_maturity_date) if loan.original_maturity_date else ""
        ),
        risk_metrics=RiskMetrics(
            ltv=loan.ltv_current,
            dscr=loan.dscr_current,
            debt_yield=loan.debt_yield_current
        ),
        pricing_results=PricingResults(
            market_yield=loan.market_yield,
            fair_value=None,  # Would need to be calculated or retrieved from view
            price=None,  # Would need to be calculated or retrieved from view
            wal=None,  # Would need to be calculated or retrieved from view
            modified_duration=None  # Would need to be calculated or retrieved from view
        )
    )

@router.post("/", response_model=LoanResponse)
async def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db)):
    """Create a new loan."""
    # Check if loan with this rp_system_id already exists
    existing_loan = db.query(Loan).filter(Loan.rp_system_id == loan_data.rp_system_id).first()
    if existing_loan:
        raise HTTPException(status_code=400, detail="Loan with this rp_system_id already exists")
    
    # Extract property locations if provided
    property_locations = loan_data.property_locations
    loan_dict = loan_data.dict(exclude={'property_locations'})
    
    # Create loan
    db_loan = Loan(**loan_dict)
    db.add(db_loan)
    db.flush()  # Flush to get the loan committed without ending transaction
    
    # Create property locations if provided
    if property_locations:
        for idx, location in enumerate(property_locations):
            db_property = LoanProperty(
                rp_system_id=db_loan.rp_system_id,
                property_number=idx + 1,
                **location.dict()
            )
            db.add(db_property)
    
    db.commit()
    db.refresh(db_loan)
    return db_loan

@router.put("/{rp_system_id}", response_model=LoanResponse)
async def update_loan(rp_system_id: int, loan_update: LoanUpdate, db: Session = Depends(get_db)):
    """Update a loan by rp_system_id."""
    db_loan = db.query(Loan).filter(Loan.rp_system_id == rp_system_id).first()
    if not db_loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Update loan fields
    update_data = loan_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_loan, field, value)
    
    db.commit()
    db.refresh(db_loan)
    return db_loan

@router.put("/by-system-id/{rp_system_id}", response_model=LoanResponse, operation_id="update_loan_by_system_id")
async def update_loan_by_system_id(rp_system_id: int, loan_update: LoanUpdate, db: Session = Depends(get_db)):
    """Update a loan by rp_system_id (alternative endpoint)."""
    return await update_loan(rp_system_id, loan_update, db)

@router.delete("/{rp_system_id}")
async def delete_loan(rp_system_id: int, db: Session = Depends(get_db)):
    """Delete a loan and its associated properties."""
    db_loan = db.query(Loan).filter(Loan.rp_system_id == rp_system_id).first()
    if not db_loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    db.delete(db_loan)
    db.commit()
    return {"message": "Loan deleted successfully"}
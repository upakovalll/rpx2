"""
Pydantic schemas for Portfolio API.
"""

from pydantic import BaseModel, RootModel
from datetime import datetime, date
from typing import Optional, List, Union, Dict
from uuid import UUID


class PortfolioBase(BaseModel):
    """Base schema for Portfolio."""
    portfolio_name: str
    source_file: Optional[str] = None
    total_loans: int = 0
    analysis_date: date
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    """Schema for creating a Portfolio."""
    user_id: UUID


class PortfolioUpdate(BaseModel):
    """Schema for updating a Portfolio."""
    portfolio_name: Optional[str] = None
    source_file: Optional[str] = None
    total_loans: Optional[int] = None
    analysis_date: Optional[date] = None
    description: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    """Schema for Portfolio responses."""
    portfolio_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 


class PortfolioSummaryGroup(BaseModel):
    name: str
    balance: float
    count: int
    percentage: float

class PortfolioSummaryResponse(BaseModel):
    total_balance: float
    loan_count: int
    average_yield: float
    weighted_average_life: float
    groupings: List[PortfolioSummaryGroup] 

class PortfolioRiskMetricsResponse(BaseModel):
    average_ltv: float
    average_dscr: float
    watchlist_count: int
    default_count: int
    expected_loss: float
    risk_distribution: Optional[list] = None 

class BenchmarkRate(BaseModel):
    benchmark_type: str
    tenor: Optional[str] = None
    rate: float
    date: Optional[str] = None

class BenchmarkRateWithId(BenchmarkRate):
    id: int
    currency: Optional[str] = "USD"
    source: Optional[str] = None
    created_at: Optional[datetime] = None

class BenchmarkRateCreate(BaseModel):
    benchmark_date: date
    benchmark_type: str
    term_years: float
    rate: float
    currency: Optional[str] = "USD"
    source: Optional[str] = None

class BenchmarkRateDetailResponse(BaseModel):
    id: int
    benchmark_date: date
    benchmark_type: str
    term_years: float
    rate: float
    currency: str
    source: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BenchmarkRateResponse(RootModel[List[BenchmarkRate]]):
    pass

class BenchmarkRateUpdate(BaseModel):
    effective_date: str
    rates: Union[Dict[str, float], List[BenchmarkRate]]  # Support both dict and list formats
    source: Optional[str] = None

class BenchmarkBulkUploadRequest(BaseModel):
    benchmark_type: str
    file: str  # path or file content (for real implementation, use UploadFile)
    validate_only: Optional[bool] = False

class BenchmarkBulkUploadResponse(BaseModel):
    message: str
    records_processed: int
    records_inserted: int
    records_updated: int
    validation_errors: Optional[List[dict]] = None 

class CreditSpread(BaseModel):
    property_sector: str
    term_bucket: Optional[str] = None
    spread_bps: int
    date: Optional[str] = None
    rating_adjustment: Optional[dict] = None
    notes: Optional[str] = None

class CreditSpreadWithId(CreditSpread):
    id: int
    source_column: Optional[str] = None
    created_at: Optional[datetime] = None

class CreditSpreadCreate(BaseModel):
    pricing_date: date
    property_type: str
    loan_class: str
    spread_bps: int  # Will be converted to decimal (divide by 10000)
    source_column: Optional[str] = None

class CreditSpreadDetailResponse(BaseModel):
    id: int
    pricing_date: date
    property_type: str
    loan_class: str
    spread: float  # Stored as decimal in DB
    spread_bps: int  # Computed from spread * 10000
    source_column: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CreditSpreadResponse(RootModel[List[CreditSpread]]):
    pass

class CreditSpreadUpdate(BaseModel):
    effective_date: str
    spreads: List[CreditSpread]
    notes: Optional[str] = None

class CreditSpreadBulkUploadRequest(BaseModel):
    effective_date: str
    file: str  # path or file content (for real implementation, use UploadFile)
    validate_only: Optional[bool] = False

class CreditSpreadBulkUploadResponse(BaseModel):
    message: str
    records_processed: int
    records_inserted: int
    records_updated: int
    validation_errors: Optional[List[dict]] = None 
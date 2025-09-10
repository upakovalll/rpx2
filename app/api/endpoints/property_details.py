"""
Property Details API endpoints for managing detailed property information.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from app.database.session import get_db

router = APIRouter()


class PropertyDetailsBase(BaseModel):
    """Base schema for property details."""
    loan_id: int = Field(..., description="Loan ID (rp_system_id)")
    property_name: str = Field(..., description="Property name")
    property_address: Optional[str] = Field(None, description="Street address")
    property_city: Optional[str] = Field(None, description="City")
    property_state: Optional[str] = Field(None, description="State/Province")
    property_zip: Optional[str] = Field(None, description="ZIP/Postal code")
    property_country: Optional[str] = Field("USA", description="Country")
    msa: Optional[str] = Field(None, description="Metropolitan Statistical Area")
    submarket: Optional[str] = Field(None, description="Submarket")
    latitude: Optional[Decimal] = Field(None, description="Latitude coordinate")
    longitude: Optional[Decimal] = Field(None, description="Longitude coordinate")
    year_built: Optional[int] = Field(None, description="Year built")
    year_renovated: Optional[int] = Field(None, description="Year renovated")
    gross_square_feet: Optional[Decimal] = Field(None, description="Gross square feet")
    net_rentable_square_feet: Optional[Decimal] = Field(None, description="Net rentable square feet")
    land_area_acres: Optional[Decimal] = Field(None, description="Land area in acres")
    number_of_units: Optional[int] = Field(None, description="Number of units")
    number_of_buildings: Optional[int] = Field(None, description="Number of buildings")
    number_of_floors: Optional[int] = Field(None, description="Number of floors")
    parking_spaces: Optional[int] = Field(None, description="Number of parking spaces")
    property_subtype: Optional[str] = Field(None, description="Property subtype")
    property_class: Optional[str] = Field(None, description="Property class (A, B, C)")
    construction_type: Optional[str] = Field(None, description="Construction type")
    number_of_tenants: Optional[int] = Field(None, description="Number of tenants")
    anchor_tenant: Optional[str] = Field(None, description="Anchor tenant name")
    largest_tenant: Optional[str] = Field(None, description="Largest tenant name")
    environmental_report_date: Optional[str] = Field(None, description="Environmental report date")
    environmental_issues: Optional[str] = Field(None, description="Environmental issues")
    leed_certification: Optional[str] = Field(None, description="LEED certification")
    energy_star_score: Optional[int] = Field(None, description="Energy Star score")


class PropertyDetailsCreate(PropertyDetailsBase):
    """Schema for creating property details."""
    pass


class PropertyDetailsUpdate(BaseModel):
    """Schema for updating property details."""
    property_name: Optional[str] = None
    property_address: Optional[str] = None
    property_city: Optional[str] = None
    property_state: Optional[str] = None
    property_zip: Optional[str] = None
    property_country: Optional[str] = None
    msa: Optional[str] = None
    submarket: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    year_built: Optional[int] = None
    year_renovated: Optional[int] = None
    gross_square_feet: Optional[Decimal] = None
    net_rentable_square_feet: Optional[Decimal] = None
    land_area_acres: Optional[Decimal] = None
    number_of_units: Optional[int] = None
    number_of_buildings: Optional[int] = None
    number_of_floors: Optional[int] = None
    parking_spaces: Optional[int] = None
    property_subtype: Optional[str] = None
    property_class: Optional[str] = None
    construction_type: Optional[str] = None
    number_of_tenants: Optional[int] = None
    anchor_tenant: Optional[str] = None
    largest_tenant: Optional[str] = None
    environmental_report_date: Optional[str] = None
    environmental_issues: Optional[str] = None
    leed_certification: Optional[str] = None
    energy_star_score: Optional[int] = None


class PropertyDetailsResponse(PropertyDetailsBase):
    """Schema for property details responses."""
    property_id: int
    created_at: Optional[str] = None


@router.get("/", operation_id="list_property_details")
async def get_property_details(
    loan_id: Optional[int] = Query(None, description="Filter by loan ID"),
    property_state: Optional[str] = Query(None, description="Filter by state"),
    property_city: Optional[str] = Query(None, description="Filter by city"),
    msa: Optional[str] = Query(None, description="Filter by MSA"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get property details with optional filters."""
    
    query = "SELECT * FROM property_details WHERE 1=1"
    params = {}
    
    if loan_id:
        query += " AND loan_id = :loan_id"
        params["loan_id"] = loan_id
    
    if property_state:
        query += " AND property_state = :property_state"
        params["property_state"] = property_state
    
    if property_city:
        query += " AND property_city = :property_city"
        params["property_city"] = property_city
    
    if msa:
        query += " AND msa = :msa"
        params["msa"] = msa
    
    query += " ORDER BY loan_id, property_name"
    query += f" LIMIT {limit} OFFSET {skip}"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.get("/loan/{loan_id}", operation_id="get_property_details_by_loan")
async def get_property_details_by_loan(
    loan_id: int,
    db: Session = Depends(get_db)
):
    """Get all property details for a specific loan."""
    
    result = db.execute(
        text("SELECT * FROM property_details WHERE loan_id = :loan_id ORDER BY property_name"),
        {"loan_id": loan_id}
    ).mappings().all()
    
    if not result:
        return JSONResponse(content=[])
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.get("/{property_id}", operation_id="get_property_detail")
async def get_property_detail(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific property detail by ID."""
    
    result = db.execute(
        text("SELECT * FROM property_details WHERE property_id = :property_id"),
        {"property_id": property_id}
    ).mappings().first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Property details not found")
    
    return JSONResponse(content=jsonable_encoder(dict(result)))


@router.post("/", operation_id="create_property_details")
async def create_property_details(
    property_data: PropertyDetailsCreate,
    db: Session = Depends(get_db)
):
    """Create new property details."""
    
    try:
        # Get next property_id
        max_id_result = db.execute(
            text("SELECT COALESCE(MAX(property_id), 0) + 1 as next_id FROM property_details")
        ).first()
        next_id = max_id_result.next_id
        
        # Build insert query dynamically based on provided fields
        columns = ["property_id", "loan_id", "property_name"]
        values = [":property_id", ":loan_id", ":property_name"]
        params = {
            "property_id": next_id,
            "loan_id": property_data.loan_id,
            "property_name": property_data.property_name
        }
        
        # Add optional fields if provided
        optional_fields = [
            "property_address", "property_city", "property_state", "property_zip",
            "property_country", "msa", "submarket", "latitude", "longitude",
            "year_built", "year_renovated", "gross_square_feet", "net_rentable_square_feet",
            "land_area_acres", "number_of_units", "number_of_buildings", "number_of_floors",
            "parking_spaces", "property_subtype", "property_class", "construction_type",
            "number_of_tenants", "anchor_tenant", "largest_tenant", "environmental_report_date",
            "environmental_issues", "leed_certification", "energy_star_score"
        ]
        
        for field in optional_fields:
            value = getattr(property_data, field, None)
            if value is not None:
                columns.append(field)
                values.append(f":{field}")
                params[field] = value
        
        query = f"""
            INSERT INTO property_details ({', '.join(columns)})
            VALUES ({', '.join(values)})
            RETURNING *
        """
        
        result = db.execute(text(query), params).mappings().first()
        db.commit()
        
        return JSONResponse(content=jsonable_encoder(dict(result)))
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{property_id}", operation_id="update_property_details")
async def update_property_details(
    property_id: int,
    property_update: PropertyDetailsUpdate,
    db: Session = Depends(get_db)
):
    """Update existing property details."""
    
    # Check if property exists
    existing = db.execute(
        text("SELECT property_id FROM property_details WHERE property_id = :property_id"),
        {"property_id": property_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Property details not found")
    
    # Build update query dynamically
    update_fields = []
    params = {"property_id": property_id}
    
    for field, value in property_update.dict(exclude_unset=True).items():
        update_fields.append(f"{field} = :{field}")
        params[field] = value
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    query = f"""
        UPDATE property_details 
        SET {', '.join(update_fields)}
        WHERE property_id = :property_id
        RETURNING *
    """
    
    result = db.execute(text(query), params).mappings().first()
    db.commit()
    
    return JSONResponse(content=jsonable_encoder(dict(result)))


@router.delete("/{property_id}", operation_id="delete_property_details")
async def delete_property_details(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Delete property details."""
    
    # Check if property exists
    existing = db.execute(
        text("SELECT property_id FROM property_details WHERE property_id = :property_id"),
        {"property_id": property_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Property details not found")
    
    # Delete property
    db.execute(
        text("DELETE FROM property_details WHERE property_id = :property_id"),
        {"property_id": property_id}
    )
    db.commit()
    
    return {"message": "Property details deleted successfully"}


@router.post("/bulk", operation_id="bulk_create_property_details")
async def bulk_create_property_details(
    properties: List[PropertyDetailsCreate],
    db: Session = Depends(get_db)
):
    """Bulk create property details."""
    
    try:
        created_count = 0
        
        for property_data in properties:
            # Get next property_id
            max_id_result = db.execute(
                text("SELECT COALESCE(MAX(property_id), 0) + 1 as next_id FROM property_details")
            ).first()
            next_id = max_id_result.next_id
            
            # Insert property
            db.execute(text("""
                INSERT INTO property_details 
                (property_id, loan_id, property_name, property_address, property_city, 
                 property_state, property_zip, property_country, msa, submarket,
                 latitude, longitude, year_built, year_renovated, gross_square_feet,
                 net_rentable_square_feet, land_area_acres)
                VALUES 
                (:property_id, :loan_id, :property_name, :property_address, :property_city,
                 :property_state, :property_zip, :property_country, :msa, :submarket,
                 :latitude, :longitude, :year_built, :year_renovated, :gross_square_feet,
                 :net_rentable_square_feet, :land_area_acres)
            """), {
                "property_id": next_id,
                "loan_id": property_data.loan_id,
                "property_name": property_data.property_name,
                "property_address": property_data.property_address,
                "property_city": property_data.property_city,
                "property_state": property_data.property_state,
                "property_zip": property_data.property_zip,
                "property_country": property_data.property_country,
                "msa": property_data.msa,
                "submarket": property_data.submarket,
                "latitude": property_data.latitude,
                "longitude": property_data.longitude,
                "year_built": property_data.year_built,
                "year_renovated": property_data.year_renovated,
                "gross_square_feet": property_data.gross_square_feet,
                "net_rentable_square_feet": property_data.net_rentable_square_feet,
                "land_area_acres": property_data.land_area_acres
            })
            created_count += 1
        
        db.commit()
        return {"message": f"Successfully created {created_count} property details"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
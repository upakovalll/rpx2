"""
Loan Property database model - Updated to match actual database schema.
"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base


class LoanProperty(Base):
    """Loan Property model matching the actual database schema."""
    
    __tablename__ = "loan_properties"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to loans
    rp_system_id = Column(BigInteger, ForeignKey("loans.rp_system_id", ondelete="CASCADE"))
    
    # Property information
    property_number = Column(Integer, default=1)
    street = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(100), default='United States')
    region = Column(String(100))
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    loan = relationship("Loan", back_populates="loan_properties")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('rp_system_id', 'property_number', name='loan_properties_rp_system_id_property_number_key'),
    )
    
    def __repr__(self):
        return f"<LoanProperty(id={self.id}, rp_system_id='{self.rp_system_id}', property_number={self.property_number})>"
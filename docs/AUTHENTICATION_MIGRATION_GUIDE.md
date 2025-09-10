# Authentication Migration Guide

This guide shows how to add authentication to existing endpoints in the RPX Backend.

## Quick Migration Examples

### 1. Protecting All Loan Endpoints

To protect all loan endpoints when authentication is enabled, modify `app/api/endpoints/loans.py`:

```python
from app.core.auth import get_current_user_optional, get_current_user
from app.core.auth_config import auth_config

# At the top of each endpoint, add:
@router.get("/")
async def get_loans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Optional[dict] = Depends(get_current_user_optional),  # Add this
    db: Session = Depends(get_db)
):
    # Check if auth is required
    if auth_config.AUTHENTICATION_ENABLED and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Rest of your code...
```

### 2. Protecting Only Write Operations

Keep read operations public but protect create/update/delete:

```python
# Public read
@router.get("/")
async def get_loans(db: Session = Depends(get_db)):
    # No authentication required
    pass

# Protected write
@router.post("/")
async def create_loan(
    loan_data: LoanCreate,
    current_user: dict = Depends(get_current_user),  # Requires auth
    db: Session = Depends(get_db)
):
    # User must be authenticated
    pass
```

### 3. Role-Based Protection

Different access levels for different operations:

```python
from app.core.auth import require_role

# Anyone can read
@router.get("/")
async def get_loans(db: Session = Depends(get_db)):
    pass

# Only managers can create
@router.post("/")
async def create_loan(
    loan_data: LoanCreate,
    current_user: dict = Depends(require_role("manager")),
    db: Session = Depends(get_db)
):
    pass

# Only admins can delete
@router.delete("/{loan_id}")
async def delete_loan(
    loan_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    pass
```

### 4. Conditional Authentication Based on Data

Protect sensitive data while keeping basic info public:

```python
@router.get("/{loan_id}")
async def get_loan(
    loan_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    loan = db.query(Loan).filter(Loan.rp_system_id == loan_id).first()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Public users see limited data
    if not current_user:
        return {
            "id": loan.rp_system_id,
            "status": loan.loan_status,
            "property_type": loan.property_type
        }
    
    # Authenticated users see full data
    return loan
```

## Migration Strategy

### Phase 1: Preparation (No Breaking Changes)
1. Add authentication system (already done)
2. Keep `AUTHENTICATION_ENABLED=false`
3. Add optional auth to endpoints
4. Test thoroughly

### Phase 2: Soft Launch
1. Enable auth in staging environment
2. Provide API keys to existing integrations
3. Monitor for issues
4. Update client applications

### Phase 3: Full Migration
1. Set `AUTHENTICATION_ENABLED=true` in production
2. Require authentication for sensitive endpoints
3. Implement proper user management
4. Add audit logging

## Endpoint Protection Patterns

### Pattern 1: Global Protection (via Middleware)
All endpoints protected except those in `PUBLIC_ENDPOINTS` list.

### Pattern 2: Selective Protection (via Dependencies)
```python
# Mix of public and protected in same router
@router.get("/public-summary")
async def get_summary():
    # No auth required
    pass

@router.get("/detailed-report")
async def get_report(current_user: dict = Depends(get_current_user)):
    # Auth required
    pass
```

### Pattern 3: Dynamic Protection
```python
@router.get("/data")
async def get_data(
    require_auth: bool = Query(False),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    if require_auth and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return data based on auth status
    if current_user:
        return {"data": "sensitive data", "user": current_user["username"]}
    else:
        return {"data": "public data only"}
```

## Testing Your Migration

### 1. Test with Auth Disabled (Default)
```bash
# Should work without changes
curl http://localhost:8000/api/v1/loans/
```

### 2. Test with Auth Enabled
```bash
# Enable in .env: AUTHENTICATION_ENABLED=true

# Should fail
curl http://localhost:8000/api/v1/loans/

# Should work with token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/loans/
```

### 3. Test Role-Based Access
```bash
# Login as user (not admin)
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=user&password=user123" | jq -r '.access_token')

# Should fail on admin-only endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/admin-endpoint/
```

## Best Practices

1. **Start with Optional Auth**: Use `get_current_user_optional` initially
2. **Test Thoroughly**: Ensure endpoints work with and without auth
3. **Document Changes**: Update API documentation
4. **Version Your API**: Consider `/api/v2/` for breaking changes
5. **Provide Migration Period**: Give clients time to update
6. **Monitor Usage**: Log authentication failures for debugging
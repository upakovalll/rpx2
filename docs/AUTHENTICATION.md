# Authentication System Documentation

## Overview

The RPX Backend 2026 includes a flexible authentication system that can be enabled or disabled through configuration. By default, authentication is **DISABLED** to allow easy development and testing. The system supports multiple authentication methods including JWT tokens and API keys.

## Table of Contents

1. [Configuration](#configuration)
2. [Authentication Methods](#authentication-methods)
3. [Enabling Authentication](#enabling-authentication)
4. [Protecting Endpoints](#protecting-endpoints)
5. [User Management](#user-management)
6. [Testing Authentication](#testing-authentication)
7. [Security Best Practices](#security-best-practices)

## Configuration

Authentication is controlled through environment variables. Create or update your `.env` file:

```env
# Master authentication switch (default: false)
AUTHENTICATION_ENABLED=false

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Key Authentication (optional)
API_KEY_ENABLED=false
MASTER_API_KEY=your-master-api-key-here

# Role-Based Access Control
RBAC_ENABLED=false

# Session Configuration
SESSION_TIMEOUT_MINUTES=60
CONCURRENT_SESSIONS_ALLOWED=true

# CORS Settings
ENABLE_CORS=true
CORS_ORIGINS=*

# OAuth2 (future implementation)
OAUTH2_ENABLED=false
```

## Authentication Methods

### 1. JWT Token Authentication

The primary authentication method using JSON Web Tokens:

- **Access Token**: Short-lived token (30 minutes default) for API access
- **Refresh Token**: Long-lived token (7 days default) to obtain new access tokens

### 2. API Key Authentication

Alternative authentication using API keys in headers:

- Header name: `X-API-Key`
- Useful for server-to-server communication
- Can be used alongside JWT authentication

## Enabling Authentication

### Quick Start

1. **Enable authentication in `.env`**:
   ```env
   AUTHENTICATION_ENABLED=true
   JWT_SECRET_KEY=your-secure-secret-key-here
   ```

2. **Restart the application**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

3. **Login to get tokens**:
   ```bash
   # Using default demo credentials
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
   ```

   Response:
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "token_type": "bearer"
   }
   ```

4. **Use the token in requests**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/loans/" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Demo Users

For testing purposes, the following users are available:

- **Admin**: username: `admin`, password: `admin123`
- **User**: username: `user`, password: `user123`

**Note**: In production, implement proper user storage in the database.

## Protecting Endpoints

### Method 1: Using Dependencies

```python
from fastapi import Depends
from app.core.auth import get_current_user, require_role

# Require authentication
@router.get("/protected")
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}"}

# Require specific role
@router.get("/admin-only")
async def admin_endpoint(current_user: dict = Depends(require_role("admin"))):
    return {"message": "Admin access granted"}
```

### Method 2: Optional Authentication

```python
from app.core.auth import get_current_user_optional

@router.get("/public-or-private")
async def flexible_endpoint(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    if current_user:
        return {"message": f"Hello {current_user['username']}"}
    else:
        return {"message": "Hello anonymous"}
```

### Method 3: Global Middleware

When `AUTHENTICATION_ENABLED=true`, the middleware automatically protects all endpoints except those in `PUBLIC_ENDPOINTS` list.

Public endpoints by default:
- `/` - Root
- `/health` - Health check
- `/docs` - Swagger UI
- `/redoc` - ReDoc
- `/api/v1/auth/*` - Auth endpoints
- `/mcp/*` - MCP endpoints

## User Management

### Check Authentication Status

```bash
curl -X GET "http://localhost:8000/api/v1/auth/status"
```

### Register New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePass123!"
  }'
```

### Get Current User Info

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Access Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Change Password

```bash
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "current_password",
    "new_password": "NewSecurePass123!"
  }'
```

## Testing Authentication

### 1. Test Without Authentication (Default)

```bash
# Should work without any auth headers
curl -X GET "http://localhost:8000/api/v1/loans/"
```

### 2. Test With Authentication Enabled

```bash
# Enable auth in .env first
AUTHENTICATION_ENABLED=true

# This should return 401 Unauthorized
curl -X GET "http://localhost:8000/api/v1/loans/"

# Login first
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# Now this should work
curl -X GET "http://localhost:8000/api/v1/loans/" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Test API Key Authentication

```bash
# Enable API key auth
API_KEY_ENABLED=true
MASTER_API_KEY=test-api-key-12345

# Use API key in header
curl -X GET "http://localhost:8000/api/v1/loans/" \
  -H "X-API-Key: test-api-key-12345"
```

## Security Best Practices

### 1. Environment Configuration

- **Never commit** `.env` files with real secrets
- Use strong, unique `JWT_SECRET_KEY` in production
- Rotate secrets regularly
- Use environment-specific configurations

### 2. Password Requirements

Default password requirements (configurable):
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### 3. Token Management

- Keep access tokens short-lived (30 minutes)
- Implement token blacklisting for logout
- Use HTTPS in production
- Store tokens securely on client side

### 4. CORS Configuration

```env
# Development
CORS_ORIGINS=*

# Production - specify allowed origins
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

### 5. Rate Limiting

Consider implementing rate limiting for auth endpoints:
- Login attempts: 5 per minute
- Registration: 3 per hour
- Password reset: 3 per hour

## Integration Examples

### Python Client

```python
import requests

class RPXClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
    
    def login(self, username, password):
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data
    
    def get_loans(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = requests.get(
            f"{self.base_url}/api/v1/loans/",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = RPXClient()
client.login("admin", "admin123")
loans = client.get_loans()
```

### JavaScript/TypeScript

```typescript
class RPXClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async login(username: string, password: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password })
    });
    
    const data = await response.json();
    this.token = data.access_token;
  }

  async getLoans(): Promise<any[]> {
    const headers: HeadersInit = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    const response = await fetch(`${this.baseUrl}/api/v1/loans/`, { headers });
    return response.json();
  }
}
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized Error**
   - Check if authentication is enabled
   - Verify token is included in Authorization header
   - Check if token has expired

2. **Invalid Token Error**
   - Ensure JWT_SECRET_KEY matches between token generation and validation
   - Check token format: `Bearer <token>`

3. **Registration Disabled**
   - Registration requires `AUTHENTICATION_ENABLED=true`

4. **CORS Errors**
   - Update `CORS_ORIGINS` in `.env`
   - Ensure `ENABLE_CORS=true`

## Future Enhancements

- Database-backed user management
- OAuth2 integration (Google, GitHub, etc.)
- Two-factor authentication (2FA)
- Session management and token blacklisting
- Advanced role-based permissions
- Audit logging for authentication events
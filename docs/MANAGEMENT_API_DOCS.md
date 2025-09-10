# Management API Documentation

This document describes the management endpoints implemented for the RPX Backend 2026 system.

## Overview

The management API provides comprehensive endpoints for managing tenants, users, API configurations, and analytics. All endpoints are available under the `/api/v1` prefix.

## Tenant Management

### Endpoints

- `GET /api/v1/tenants/` - List all tenants with pagination
- `GET /api/v1/tenants/overview` - Get tenant overview with API statistics
- `GET /api/v1/tenants/resource-usage` - Get resource usage statistics
- `GET /api/v1/tenants/{tenant_id}` - Get specific tenant details
- `POST /api/v1/tenants/` - Create a new tenant
- `PUT /api/v1/tenants/{tenant_id}` - Update tenant information
- `DELETE /api/v1/tenants/{tenant_id}` - Soft delete a tenant

### Example: Create Tenant
```bash
curl -X POST "http://localhost:8000/api/v1/tenants/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Tenant",
    "slug": "new-tenant",
    "subdomain": "newtenant",
    "plan": "starter",
    "settings": {
      "theme": "light",
      "language": "en"
    },
    "limits": {
      "max_users": 10,
      "max_projects": 5,
      "max_storage_gb": 20
    }
  }'
```

## User Management

### Endpoints

- `GET /api/v1/users/` - List users with filtering
- `GET /api/v1/users/summary` - Get user statistics by tenant
- `GET /api/v1/users/details` - Get detailed user information
- `GET /api/v1/users/{user_id}` - Get specific user
- `POST /api/v1/users/` - Create new user
- `PUT /api/v1/users/{user_id}` - Update user information
- `POST /api/v1/users/{user_id}/activate` - Activate user
- `POST /api/v1/users/{user_id}/deactivate` - Deactivate user
- `POST /api/v1/users/{user_id}/change-password` - Change user password

### Example: Create User
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123",
    "tenant_id": "90eebc99-9c0b-4ef8-bb6d-6bb9bd380911",
    "is_admin": false,
    "metadata": {
      "department": "Engineering"
    }
  }'
```

## API Configuration Management

### Endpoints

- `GET /api/v1/api-management/providers` - List available API providers
- `GET /api/v1/api-management/configurations` - List API configurations
- `GET /api/v1/api-management/configurations/{config_id}` - Get specific configuration
- `POST /api/v1/api-management/configurations` - Create new configuration
- `PUT /api/v1/api-management/configurations/{config_id}` - Update configuration
- `DELETE /api/v1/api-management/configurations/{config_id}` - Soft delete configuration

### API Key Management

- `GET /api/v1/api-management/keys` - List API keys with status
- `POST /api/v1/api-management/keys` - Create new API key
- `POST /api/v1/api-management/keys/{key_id}/revoke` - Revoke API key
- `POST /api/v1/api-management/keys/{key_id}/rotate` - Rotate API key

### Example: Create API Configuration
```bash
curl -X POST "http://localhost:8000/api/v1/api-management/configurations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Stripe Production",
    "tenant_id": "90eebc99-9c0b-4ef8-bb6d-6bb9bd380911",
    "provider_id": "e0eebc99-9c0b-4ef8-bb6d-6bb9bd380e21",
    "environment": "production",
    "settings": {
      "webhook_secret": "whsec_xxx",
      "api_version": "2023-10-16"
    }
  }'
```

## Analytics

### Endpoints

- `GET /api/v1/analytics/usage` - Get API usage statistics
- `GET /api/v1/analytics/performance` - Get API performance metrics
- `GET /api/v1/analytics/rate-limits` - Get current rate limit status
- `GET /api/v1/analytics/security-audit` - Get API security audit information
- `GET /api/v1/analytics/activity-timeline` - Get tenant activity timeline
- `GET /api/v1/analytics/webhook-summary` - Get webhook activity summary
- `GET /api/v1/analytics/dashboard` - Get comprehensive dashboard data

### Example: Get Analytics Dashboard
```bash
curl -s "http://localhost:8000/api/v1/analytics/dashboard?tenant_id=90eebc99-9c0b-4ef8-bb6d-6bb9bd380911"
```

## Database Views Used

The management API leverages several database views for efficient data aggregation:

- `tenant_api_overview` - Provides tenant-level API statistics
- `tenant_resource_usage` - Shows resource usage against limits
- `tenant_user_summary` - Aggregates user statistics by tenant
- `tenant_user_details` - Detailed user information with organizations
- `api_usage_statistics` - API call statistics per configuration
- `api_call_performance` - Performance metrics by endpoint
- `api_rate_limit_status` - Real-time rate limit usage
- `api_security_audit` - Security-related API information
- `tenant_activity_timeline` - Recent activity across entities

## Response Format

All endpoints return JSON responses with appropriate status codes:
- `200 OK` - Successful GET/PUT requests
- `201 Created` - Successful POST requests
- `400 Bad Request` - Invalid input data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server errors

## Pagination

List endpoints support pagination with query parameters:
- `page` - Page number (default: 1)
- `size` - Items per page (default: 10, max: 100)

Example:
```bash
curl "http://localhost:8000/api/v1/users/?page=2&size=20"
```

## Filtering

Many endpoints support filtering through query parameters:
- `tenant_id` - Filter by tenant UUID
- `is_active` - Filter by active status (true/false)
- `environment` - Filter by environment (development/staging/production)
- `plan` - Filter by tenant plan

## Error Handling

Errors are returned in a consistent format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Security Notes

1. **Authentication**: Currently disabled for development. Implement before production.
2. **API Keys**: Keys are generated server-side and returned only once during creation
3. **Passwords**: Hashed using SHA256 with salt (upgrade to bcrypt/scrypt for production)
4. **Soft Deletes**: DELETE operations perform soft deletes by setting `is_active=false`

## Testing

All endpoints have been tested and are functional. Use the provided curl examples to interact with the API.
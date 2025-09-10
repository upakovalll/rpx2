"""API routes configuration."""

from fastapi import APIRouter

from app.api.endpoints import loans, portfolios, property_locations, valuation, exports, auth, market_rates, pricing_data, fx_rates, rpx_adjustments, property_details, data_import, launch_config
from app.api.endpoints.management import tenants, users, api_management, analytics
from app.core.auth_config import auth_config

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(loans.router, prefix="/loans", tags=["loans"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(property_locations.router, prefix="/property-locations", tags=["property-locations"])
api_router.include_router(valuation.router, prefix="/valuation", tags=["valuation"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(market_rates.router, prefix="/market-rates", tags=["market-rates"])
api_router.include_router(pricing_data.router, prefix="/pricing-data", tags=["pricing-data"])
api_router.include_router(launch_config.router, prefix="/launch-config", tags=["launch-config"])
api_router.include_router(fx_rates.router, prefix="/fx-rates", tags=["fx-rates"])
api_router.include_router(rpx_adjustments.router, prefix="/rpx-adjustments", tags=["rpx-adjustments"])
api_router.include_router(property_details.router, prefix="/property-details", tags=["property-details"])
api_router.include_router(data_import.router, prefix="/data-import", tags=["data-import"])

# Include management routers
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(api_management.router, prefix="/api-management", tags=["api-management"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Include auth router (always available to check status, but endpoints work only when auth is enabled)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"]) 
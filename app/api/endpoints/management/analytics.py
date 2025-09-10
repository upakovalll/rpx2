from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import logging

from app.database.session import get_db
from app.schemas.management import (
    TenantOverview,
    APIUsageStatistics,
    APICallPerformance,
    APIRateLimitStatus,
    APISecurityAudit
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/usage", operation_id="get_api_usage")
async def get_api_usage_statistics(
    tenant_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    environment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get API usage statistics"""
    try:
        query = "SELECT * FROM api_usage_statistics WHERE 1=1"
        params = {}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if provider_id:
            query += " AND provider_name IN (SELECT name FROM api_providers WHERE id = :provider_id)"
            params['provider_id'] = str(provider_id)
            
        if environment:
            query += " AND environment = :environment"
            params['environment'] = environment
            
        query += " ORDER BY total_calls DESC"
        
        result = db.execute(text(query), params)
        usage_stats = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(usage_stats))
        
    except Exception as e:
        logger.error(f"Error getting API usage statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", operation_id="get_api_performance")
async def get_api_performance_metrics(
    tenant_id: Optional[UUID] = None,
    provider_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    min_calls: int = Query(10, description="Minimum number of calls to include endpoint"),
    db: Session = Depends(get_db)
):
    """Get API performance metrics by endpoint"""
    try:
        query = "SELECT * FROM api_call_performance WHERE call_count >= :min_calls"
        params = {"min_calls": min_calls}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if provider_name:
            query += " AND provider_name = :provider_name"
            params['provider_name'] = provider_name
            
        if endpoint:
            query += " AND endpoint LIKE :endpoint"
            params['endpoint'] = f"%{endpoint}%"
            
        query += " ORDER BY call_count DESC"
        
        result = db.execute(text(query), params)
        performance_data = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(performance_data))
        
    except Exception as e:
        logger.error(f"Error getting API performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limits", operation_id="get_rate_limits")
async def get_rate_limit_status(
    tenant_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, pattern="^(normal|warning|critical)$"),
    db: Session = Depends(get_db)
):
    """Get current rate limit usage status"""
    try:
        query = "SELECT * FROM api_rate_limit_status WHERE 1=1"
        params = {}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if status_filter:
            query += " AND rate_limit_status = :status_filter"
            params['status_filter'] = status_filter
            
        query += " ORDER BY hour_usage_percentage DESC NULLS LAST"
        
        result = db.execute(text(query), params)
        rate_limit_data = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(rate_limit_data))
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security-audit", operation_id="get_security_audit")
async def get_api_security_audit(
    tenant_id: Optional[UUID] = None,
    environment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get API security audit information"""
    try:
        query = "SELECT * FROM api_security_audit WHERE 1=1"
        params = {}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if environment:
            query += " AND environment = :environment"
            params['environment'] = environment
            
        query += " ORDER BY expired_keys DESC, expiring_soon_keys DESC"
        
        result = db.execute(text(query), params)
        audit_data = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(audit_data))
        
    except Exception as e:
        logger.error(f"Error getting security audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-timeline", operation_id="get_activity")
async def get_tenant_activity_timeline(
    tenant_id: Optional[UUID] = None,
    entity_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get recent activity timeline for tenants"""
    try:
        query = """
            SELECT * FROM tenant_activity_timeline 
            WHERE 1=1
        """
        params = {"limit": limit}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if entity_type:
            query += " AND entity_type = :entity_type"
            params['entity_type'] = entity_type
            
        query += " ORDER BY created_at DESC LIMIT :limit"
        
        result = db.execute(text(query), params)
        activities = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(activities))
        
    except Exception as e:
        logger.error(f"Error getting activity timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook-summary", operation_id="get_webhooks")
async def get_webhook_activity_summary(
    tenant_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get webhook activity summary"""
    try:
        query = """
            SELECT 
                t.id AS tenant_id,
                t.name AS tenant_name,
                ap.name AS provider_name,
                aw.webhook_url,
                aw.is_active AS webhook_active,
                COUNT(awe.id) AS total_events,
                COUNT(CASE WHEN awe.is_verified THEN 1 END) AS verified_events,
                COUNT(CASE WHEN awe.is_processed THEN 1 END) AS processed_events,
                COUNT(CASE WHEN awe.error_message IS NOT NULL THEN 1 END) AS failed_events,
                COUNT(DISTINCT awe.event_type) AS unique_event_types,
                MAX(awe.created_at) AS last_event_at,
                aw.last_triggered_at,
                STRING_AGG(DISTINCT awe.event_type, ', ' ORDER BY awe.event_type) AS event_types
            FROM api_webhooks aw
            JOIN tenants t ON aw.tenant_id = t.id
            LEFT JOIN api_providers ap ON aw.provider_id = ap.id
            LEFT JOIN api_webhook_events awe ON aw.id = awe.webhook_id
                AND awe.created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
            WHERE 1=1
        """
        params = {}
        
        if tenant_id:
            query += " AND aw.tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if provider_id:
            query += " AND aw.provider_id = :provider_id"
            params['provider_id'] = str(provider_id)
            
        if is_active is not None:
            query += " AND aw.is_active = :is_active"
            params['is_active'] = is_active
            
        query += """
            GROUP BY t.id, t.name, ap.name, aw.id, aw.webhook_url, aw.is_active, aw.last_triggered_at
            ORDER BY t.name, ap.name, aw.webhook_url
        """
        
        result = db.execute(text(query), params)
        webhook_data = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(webhook_data))
        
    except Exception as e:
        logger.error(f"Error getting webhook summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", operation_id="get_dashboard")
async def get_analytics_dashboard(
    tenant_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics dashboard data"""
    try:
        dashboard_data = {}
        
        # Tenant overview
        overview_query = "SELECT * FROM tenant_api_overview"
        if tenant_id:
            overview_query += f" WHERE tenant_id = '{tenant_id}'"
        overview_result = db.execute(text(overview_query))
        dashboard_data['tenant_overview'] = [dict(row._mapping) for row in overview_result]
        
        # Resource usage
        resource_query = "SELECT * FROM tenant_resource_usage"
        if tenant_id:
            resource_query += f" WHERE tenant_id = '{tenant_id}'"
        resource_result = db.execute(text(resource_query))
        dashboard_data['resource_usage'] = [dict(row._mapping) for row in resource_result]
        
        # Recent API performance (last 24 hours)
        perf_query = """
            SELECT 
                COUNT(*) as total_calls_24h,
                COUNT(CASE WHEN response_status >= 200 AND response_status < 300 THEN 1 END) as successful_calls_24h,
                COUNT(CASE WHEN response_status >= 400 THEN 1 END) as failed_calls_24h,
                AVG(duration_ms) as avg_duration_ms,
                MAX(duration_ms) as max_duration_ms
            FROM api_call_logs
            WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """
        if tenant_id:
            perf_query += f" AND tenant_id = '{tenant_id}'"
        perf_result = db.execute(text(perf_query))
        dashboard_data['performance_24h'] = dict(perf_result.mappings().first())
        
        # Active configurations by environment
        env_query = """
            SELECT 
                environment,
                COUNT(*) as configuration_count,
                COUNT(CASE WHEN is_active THEN 1 END) as active_count
            FROM api_configurations
            WHERE 1=1
        """
        if tenant_id:
            env_query += f" AND tenant_id = '{tenant_id}'"
        env_query += " GROUP BY environment"
        env_result = db.execute(text(env_query))
        dashboard_data['configurations_by_env'] = [dict(row._mapping) for row in env_result]
        
        # Top 5 most used APIs
        top_apis_query = """
            SELECT 
                ap.display_name as provider_name,
                COUNT(acl.id) as call_count,
                AVG(acl.duration_ms) as avg_duration_ms
            FROM api_call_logs acl
            JOIN api_configurations ac ON acl.configuration_id = ac.id
            JOIN api_providers ap ON ac.provider_id = ap.id
            WHERE acl.created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
        """
        if tenant_id:
            top_apis_query += f" AND acl.tenant_id = '{tenant_id}'"
        top_apis_query += """
            GROUP BY ap.display_name
            ORDER BY call_count DESC
            LIMIT 5
        """
        top_apis_result = db.execute(text(top_apis_query))
        dashboard_data['top_apis'] = [dict(row._mapping) for row in top_apis_result]
        
        return JSONResponse(content=jsonable_encoder(dashboard_data))
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
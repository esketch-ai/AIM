"""AIM (AI Platform Initiative) - API Routers Package
Exposes modular REST API endpoints for:
1. Core Service Engine (/api/v1/service)
2. Subscriber Tenant Portal (/api/v1/tenant)
3. Master Admin Control Plane (/api/v1/admin)
"""
from aim.api.service_router import service_router
from aim.api.tenant_router import tenant_router
from aim.api.admin_router import admin_router
from aim.api.creator_router import router as creator_router
from aim.api.orchestrator_router import router as orchestrator_router
from aim.api.monetization_router import router as monetization_router
from aim.api.consulting_router import consulting_router

__all__ = ["service_router", "tenant_router", "admin_router", "creator_router", "orchestrator_router", "monetization_router", "consulting_router"]

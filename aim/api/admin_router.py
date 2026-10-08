"""AIM (AI Platform Initiative) - Solution 3: Platform Master Admin Control Plane API Router
Exposes enterprise fleet lifecycle, FinOps (MRR/ARR), Compliance Quarantine (Human-in-the-Loop), and Agent Telemetry.
Path Prefix: /api/v1/admin
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aim.tenant.manager import TenantManager
from aim.admin.master_console import MasterAdminConsole
from aim.admin.quarantine import ComplianceQuarantineQueue
from aim.admin.fleet import FleetController, FleetMetrics, OnboardTenantRequest

admin_router = APIRouter()


class UpdateTenantStatusRequest(BaseModel):
    tenant_id: str
    status: str = Field(description="'ACTIVE', 'SUSPENDED', or 'TRIAL'")


class UpdateTenantPlanRequest(BaseModel):
    tenant_id: str
    tier: str = Field(description="'FREE', 'PRO', or 'ENTERPRISE'")


class ResolveQuarantineRequest(BaseModel):
    decision: str = Field(description="'APPROVED_BY_ADMIN' or 'REJECTED'")
    reviewer: str = Field(default="총괄 법무팀/수석 운영관")
    notes: Optional[str] = Field(default="")


@admin_router.get("/overview", summary="Executive global platform overview")
def get_admin_overview():
    """Returns global KPIs, MRR, tenant accounts, compliance logs, and pending quarantine count."""
    kpis = MasterAdminConsole.get_global_kpis()
    logs = MasterAdminConsole.get_audit_logs()
    tenants = TenantManager.list_tenants()
    quarantined = ComplianceQuarantineQueue.list_quarantined()
    pending_quarantine_count = sum(1 for q in quarantined if q.status == "PENDING")

    return {
        "kpis": kpis.model_dump(),
        "tenants": [t.model_dump() for t in tenants],
        "audit_logs": [log.model_dump() for log in logs],
        "quarantine_summary": {
            "total_flagged": len(quarantined),
            "pending_review": pending_quarantine_count,
        },
    }


@admin_router.get("/tenants", summary="List enterprise tenant fleet")
def list_fleet_tenants():
    """Returns comprehensive list of registered subscriber tenants."""
    return {"tenants": [t.model_dump() for t in TenantManager.list_tenants()]}


@admin_router.post("/tenant/status", summary="Update tenant lifecycle status")
def update_tenant_status(req: UpdateTenantStatusRequest):
    """Operator activates or suspends tenant account."""
    updated = TenantManager.update_status(req.tenant_id, req.status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Tenant '{req.tenant_id}' not found")
    return {"status": "SUCCESS", "tenant": updated.model_dump()}


@admin_router.post("/tenant/plan", summary="Admin override of subscription tier")
def update_tenant_plan(req: UpdateTenantPlanRequest):
    """Operator overrides tenant subscription tier."""
    updated = TenantManager.update_subscription_tier(req.tenant_id, req.tier)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Tenant '{req.tenant_id}' not found")
    return {"status": "SUCCESS", "tenant": updated.model_dump()}


@admin_router.get("/quarantine", summary="List compliance quarantine queue")
def list_quarantine_items(status: Optional[str] = None):
    """Returns marketing campaigns flagged for regulatory review (Human-in-the-Loop)."""
    items = ComplianceQuarantineQueue.list_quarantined(status_filter=status)
    return {"items": [item.model_dump() for item in items]}


@admin_router.post("/quarantine/{item_id}/resolve", summary="Resolve quarantined campaign item")
def resolve_quarantine_item(item_id: str, req: ResolveQuarantineRequest):
    """Operator or legal reviewer approves or rejects flagged campaign copy."""
    resolved = ComplianceQuarantineQueue.resolve_item(
        item_id=item_id,
        decision=req.decision,
        reviewer=req.reviewer,
        notes=req.notes or "",
    )
    if not resolved:
        raise HTTPException(status_code=404, detail=f"Quarantined item '{item_id}' not found")

    return {
        "status": "SUCCESS",
        "resolved_item": resolved.model_dump(),
        "message": f"아이템 '{item_id}'의 심의가 '{req.decision}'으로 최종 확정되었습니다.",
    }


@admin_router.get("/audit-logs", summary="List full compliance audit trail")
def list_audit_logs(domain: Optional[str] = None):
    """Returns chronological audit trail of all intercepted terms and sanitization actions."""
    logs = MasterAdminConsole.get_audit_logs(domain=domain)
    return {"audit_logs": [log.model_dump() for log in logs]}


# --- Fleet Operations & FinOps Endpoints ---

@admin_router.get("/fleet/metrics", summary="Get enterprise SaaS FinOps & fleet metrics")
def get_fleet_finops_metrics():
    """Returns MRR, ARR, ARPU, active tenant count, and tier/domain breakdown."""
    metrics = FleetController.get_fleet_metrics()
    return metrics.model_dump()


@admin_router.post("/fleet/onboard", summary="Onboard new tenant into enterprise fleet")
def onboard_tenant(req: OnboardTenantRequest):
    """Provisions a new business subscriber workspace, initializes business state and issues first invoice."""
    try:
        new_account = FleetController.onboard_new_tenant(req)
        return {
            "status": "SUCCESS",
            "tenant": new_account.model_dump(),
            "message": f"신규 테넌트 '{new_account.business_name}'이(가) 플릿에 정상 등록되었습니다.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

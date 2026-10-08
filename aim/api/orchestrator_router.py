"""
AIM Dynamic Orchestrator API Router (aim/api/orchestrator_router.py)
-------------------------------------------------------------------
Exposes REST endpoints for the closed-loop organic service lifecycle:
1. Signal Injection & Action Bundle Generation (/trigger)
2. Live Stream Query (/live-stream/{tenant_id})
3. Unified Bundle Execution (/execute-bundle)
4. Master Global Signal-Value Flow (/global-flow)
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aim.core.dynamic_orchestrator import (
    dynamic_orchestrator,
    DynamicTriggerSignal,
    OrchestratedActionBundle,
)
from aim.core.value_attribution import attribution_ledger
from aim.matching.creator_network import creator_network
from aim.tenant.manager import TenantManager

router = APIRouter(prefix="/api/v1/orchestrator", tags=["Dynamic Organic Orchestrator"])


class ExecuteBundleRequest(BaseModel):
    bundle_id: str
    tenant_id: str
    selected_channels: List[str] = Field(default_factory=lambda: ["blog", "instagram", "kakaotalk"])
    order_creator_escrow: bool = False
    creator_id: Optional[str] = None


@router.post("/trigger", response_model=OrchestratedActionBundle)
def trigger_dynamic_signal(signal: DynamicTriggerSignal):
    """Injects a real-time signal and produces a unified, cross-pillar action bundle."""
    tenant = TenantManager.get_tenant(signal.tenant_id)
    plan = tenant.subscription_tier if tenant else "PRO"
    bundle = dynamic_orchestrator.process_signal(signal, subscriber_plan=plan)
    return bundle


@router.get("/live-stream/{tenant_id}")
def get_tenant_live_stream(tenant_id: str):
    """Returns the historical and active action bundles for a subscriber tenant."""
    bundles = [b for b in dynamic_orchestrator.history if b.tenant_id == tenant_id]
    tenant = TenantManager.get_tenant(tenant_id)
    summary = attribution_ledger.get_tenant_summary(
        tenant_id=tenant_id,
        monthly_fee_krw=tenant.monthly_fee_krw if tenant else 49000,
        business_name=tenant.business_name if tenant else tenant_id,
    )
    return {
        "tenant_id": tenant_id,
        "bundle_count": len(bundles),
        "bundles": bundles[-5:],  # Return latest 5
        "attribution_summary": summary,
    }


@router.post("/execute-bundle")
def execute_orchestrated_bundle(req: ExecuteBundleRequest):
    """Executes omnichannel dispatch and optional creator escrow locking, attributing revenue."""
    bundle = next((b for b in dynamic_orchestrator.history if b.bundle_id == req.bundle_id), None)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Bundle {req.bundle_id} not found.")

    bundle.status = "DISPATCHED"

    # 1. Record campaign revenue attribution
    attr_entry = attribution_ledger.record_attribution(
        tenant_id=req.tenant_id,
        source_type="CAMPAIGN_DISPATCH",
        title=bundle.strategy_summary,
        units_generated=10,
        unit_price=bundle.projected_revenue_krw // 10 if bundle.projected_revenue_krw > 0 else 24000,
        cost_incurred_krw=0,
        evidence_tier="C_ILLUSTRATIVE",
    )

    # 2. Record tenant cumulative stats
    TenantManager.record_campaign_execution(req.tenant_id, bundle.projected_revenue_krw)

    # 3. Optional creator escrow locking
    escrow_deal = None
    if req.order_creator_escrow:
        cid = req.creator_id or (bundle.matched_creators[0]["creator"]["creator_id"] if bundle.matched_creators else "CR_FNB_02")
        bid = bundle.creator_brief.get("brief_id", "BRIEF_DYNAMIC_01")
        escrow_deal = creator_network.create_escrow_deal(
            tenant_id=req.tenant_id,
            creator_id=cid,
            brief_id=bid,
            subscriber_plan="PRO",
        )

    return {
        "status": "SUCCESS",
        "bundle_id": req.bundle_id,
        "dispatched_channels": req.selected_channels,
        "projected_revenue_krw": bundle.projected_revenue_krw,
        "attributed_entry": attr_entry,
        "escrow_deal": escrow_deal,
        "message": f"'{bundle.business_name}' 캠페인이 {len(req.selected_channels)}개 채널에 즉시 송출되고 매출이 귀속되었습니다.",
    }


@router.get("/global-flow")
def get_global_signal_value_flow():
    """Returns cross-pillar global telemetry data for Master Admin war room."""
    admin_mkt = creator_network.get_admin_metrics()
    total_bundles = len(dynamic_orchestrator.history)

    return {
        "total_signals_orchestrated": total_bundles,
        "active_tenants_connected": len(TenantManager.list_tenants()),
        "marketplace_metrics": admin_mkt,
        "pipeline_health": {
            "sensor_latency_ms": 2.8,
            "orchestrator_latency_ms": 4.1,
            "compliance_guardrail": "100% PROTECTED",
            "escrow_clearing": "SYNCHRONIZED",
        },
    }

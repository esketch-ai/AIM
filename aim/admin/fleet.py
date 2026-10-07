"""AIM (AI Platform Initiative) - Fleet Operations & FinOps Controller
Super-admin management of tenant fleet lifecycle, SaaS FinOps analytics (MRR/ARR/ARPU),
and automated onboarding.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from aim.schema import TenantAccount, BusinessState
from aim.tenant.manager import TenantManager
from aim.tenant.billing import BillingService


class FleetMetrics(BaseModel):
    total_tenants: int
    active_tenants: int
    paused_tenants: int
    total_mrr_krw: int
    annual_run_rate_arr_krw: int
    average_revenue_per_user_arpu_krw: int
    total_value_generated_krw: int
    platform_overall_roi: float
    domain_distribution: Dict[str, int]
    tier_distribution: Dict[str, int]


class OnboardTenantRequest(BaseModel):
    tenant_id: str
    business_name: str
    owner_name: str
    domain: str
    subscription_tier: str = "PRO"
    location: str
    target_audience: str
    core_usps: List[str]
    unit_price: int
    trigger_event: str


class FleetController:
    """Enterprise Fleet Controller managing tenant account lifecycle and FinOps metrics."""

    @classmethod
    def get_fleet_metrics(cls) -> FleetMetrics:
        tenants = TenantManager.list_tenants()
        active = [t for t in tenants if t.status == "ACTIVE"]
        paused = [t for t in tenants if t.status != "ACTIVE"]

        total_mrr = sum(t.monthly_fee_krw for t in active)
        arr = total_mrr * 12
        arpu = int(total_mrr / len(active)) if active else 0

        total_value = sum(t.cumulative_revenue_generated_krw for t in tenants)
        platform_roi = (
            round(total_value / (total_mrr * 6), 1) if total_mrr > 0 else 0.0
        )

        domains: Dict[str, int] = {}
        tiers: Dict[str, int] = {}
        for t in tenants:
            domains[t.domain] = domains.get(t.domain, 0) + 1
            tiers[t.subscription_tier] = tiers.get(t.subscription_tier, 0) + 1

        return FleetMetrics(
            total_tenants=len(tenants),
            active_tenants=len(active),
            paused_tenants=len(paused),
            total_mrr_krw=total_mrr,
            annual_run_rate_arr_krw=arr,
            average_revenue_per_user_arpu_krw=arpu,
            total_value_generated_krw=total_value,
            platform_overall_roi=platform_roi,
            domain_distribution=domains,
            tier_distribution=tiers,
        )

    @classmethod
    def onboard_new_tenant(cls, req: OnboardTenantRequest) -> TenantAccount:
        """Onboards new subscriber business into the tenant fleet and issues initial invoice."""
        fee = 199000 if req.subscription_tier == "ENTERPRISE" else (49000 if req.subscription_tier == "PRO" else 0)
        
        bstate = BusinessState(
            domain=req.domain,
            entity_name=req.business_name,
            location=req.location,
            target_audience=req.target_audience,
            core_usps=req.core_usps,
            unit_price=req.unit_price,
            trigger_event=req.trigger_event,
            idle_capacity_rate=0.25,
            pending_leads_count=10,
        )

        account = TenantAccount(
            tenant_id=req.tenant_id,
            business_name=req.business_name,
            owner_name=req.owner_name,
            domain=req.domain,
            subscription_tier=req.subscription_tier,
            monthly_fee_krw=fee,
            status="ACTIVE",
            joined_at="2026-10-07",
            business_state=bstate,
            cumulative_revenue_generated_krw=0,
            total_campaigns_executed=0,
        )

        # Register in manager
        TenantManager._initialize_defaults()
        TenantManager._tenants[req.tenant_id] = account

        # Generate initial subscription invoice
        BillingService.create_invoice(req.tenant_id, req.subscription_tier)

        return account

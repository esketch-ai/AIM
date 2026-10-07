"""AIM (AI Platform Initiative) - Solution 1: Core Service Engine API Router
Exposes autonomous 6D sensing, campaign planning, omni-channel dispatch, and testbed simulation.
Path Prefix: /api/v1/service
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from aim.schema import BusinessState, CampaignPlan, EvidenceTier
from aim.core.platform import AIMPlatform
from aim.testbed_engine import IndustryTestbedEngine
from aim.intelligence import LocalIntelligenceEngine

service_router = APIRouter()
testbed_engine = IndustryTestbedEngine()


class PlanCampaignRequest(BaseModel):
    business_state: BusinessState


class ExecuteCampaignRequest(BaseModel):
    campaign_plan: CampaignPlan
    selected_channels: Optional[List[str]] = None


class SimulateTestbedRequest(BaseModel):
    industry_id: str
    custom_context: Optional[Dict[str, Any]] = None


@service_router.post("/plan", summary="Generate 6D-driven campaign plan")
def plan_campaign(req: PlanCampaignRequest):
    """Executes 6D hyper-context sensing, domain strategy determination, and compliance filtering."""
    try:
        plan = AIMPlatform.plan_campaign(req.business_state)
        return plan.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@service_router.post("/execute", summary="Dispatch campaign to omni-channels")
def execute_campaign(req: ExecuteCampaignRequest):
    """Executes multi-channel delivery for an approved campaign plan."""
    try:
        result = AIMPlatform.execute_campaign(req.campaign_plan, req.selected_channels)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@service_router.get("/industries", summary="List supported testbed industries")
def list_industries():
    """Returns catalog of testbed domains (F&B, Medical, Beauty, SaaS, Manufacturing)."""
    return {"industries": testbed_engine.list_industries()}


@service_router.get("/industries/{industry_id}", summary="Get industry testbed state")
def get_industry_profile(industry_id: str):
    """Returns 6D context and simulated baseline actions for specified industry."""
    profile = testbed_engine.get_industry(industry_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Industry '{industry_id}' not found")
    return profile.model_dump()


@service_router.post("/simulate", summary="Simulate dynamic context changes on testbed")
def simulate_action(req: SimulateTestbedRequest):
    """Injects custom context triggers (weather, no-show, stock) and recalculates actions."""
    try:
        profile = testbed_engine.simulate_action(req.industry_id, req.custom_context)
        return profile.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@service_router.get("/intelligence", summary="Local market & competitor radar")
def get_market_intelligence(store_name: str = Query("성수 아뜰리에 베이커리 & 카페")):
    """Returns competitor radar, flash revenue booster, and search rank diagnostics."""
    competitors = LocalIntelligenceEngine.get_competitor_radar()
    booster = LocalIntelligenceEngine.generate_flash_booster(store_name)
    ranking = LocalIntelligenceEngine.diagnose_search_rank(store_name)

    return {
        "store_name": store_name,
        "competitors": [c.model_dump() for c in competitors],
        "flash_booster": booster.model_dump(),
        "ranking_diagnosis": ranking.model_dump(),
    }

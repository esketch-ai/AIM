"""
AIM Creator & Marketplace API Router (aim/api/creator_router.py)
----------------------------------------------------------------
Provides REST APIs for:
1. Value Compression (3s Hook + 15s Pitch + Single CTA)
2. Standardized Brief Generation from 3 merchant questions
3. On-demand algorithmic creator matching with audience metrics
4. Escrow contract creation, subscriber fee discount, and 24h review SLA
5. Master admin marketplace take-rate metrics
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from aim.core.value_compressor import ValueCompressor, ValueCompressionRequest
from aim.core.brief_generator import BriefGenerator, BriefQuestionnaireInput
from aim.matching.creator_network import (
    creator_network,
    MatchRequest,
    EscrowDeal,
)

router = APIRouter(prefix="/api/v1/creator", tags=["Creator Marketplace"])

compressor = ValueCompressor()
brief_gen = BriefGenerator()


class ReviewRequest(BaseModel):
    action: str  # APPROVE, REVISE, SETTLE
    feedback: Optional[str] = None


class EscrowOrderRequest(BaseModel):
    tenant_id: str
    creator_id: str
    brief_id: str
    subscriber_plan: str = "PRO"


@router.post("/value/compress")
def compress_value(req: ValueCompressionRequest):
    """Compresses merchant value proposition into 3s hook, hard numbers, and direct single CTA."""
    return compressor.compress(req)


@router.post("/brief/generate")
def generate_standardized_brief(inp: BriefQuestionnaireInput):
    """Generates a ready-to-shoot 15s standardized creator brief from 3 essential merchant questions."""
    return brief_gen.generate(inp)


@router.post("/match")
def match_creators(req: MatchRequest):
    """Returns top ranked creators matching category, audience affinity, and conversion rating."""
    matches = creator_network.match_creators(req)
    return {
        "status": "success",
        "total_matched": len(matches),
        "target_audience": req.target_audience,
        "subscriber_discount_applied": req.subscriber_plan.upper() in ["PRO", "ENTERPRISE"],
        "take_rate_pct": 10.0 if req.subscriber_plan.upper() in ["PRO", "ENTERPRISE"] else 15.0,
        "creators": matches,
    }


@router.post("/escrow/order")
def create_escrow_order(req: EscrowOrderRequest):
    """Locks escrow payment for matched creator with 10% subscriber discount and generates contract deal."""
    deal = creator_network.create_escrow_deal(
        tenant_id=req.tenant_id,
        creator_id=req.creator_id,
        brief_id=req.brief_id,
        subscriber_plan=req.subscriber_plan,
    )
    return {
        "status": "success",
        "message": "제작비가 AIM 안전 에스크로 계좌에 예치되었습니다. 크리에이터에게 표준 브리프가 즉시 발송되었습니다.",
        "deal": deal,
    }


@router.post("/deal/{deal_id}/review")
def review_deal(deal_id: str, req: ReviewRequest):
    """Handles fast-track 24h review (Approve, Revise max 1 time, or Settle)."""
    try:
        updated_deal = creator_network.review_deal(deal_id=deal_id, action=req.action, feedback=req.feedback)
        return {
            "status": "success",
            "message": f"딜 상태가 '{updated_deal.status}'(으)로 갱신되었습니다.",
            "deal": updated_deal,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deals/{tenant_id}")
def get_tenant_deals(tenant_id: str):
    """Returns all active escrow deals for a given merchant tenant."""
    deals = [d for d in creator_network.active_deals.values() if d.tenant_id == tenant_id]
    return {
        "tenant_id": tenant_id,
        "deal_count": len(deals),
        "deals": deals,
    }


@router.get("/admin/overview")
def get_marketplace_admin_overview():
    """Returns marketplace gross merchandise volume, active escrow deals, and platform take-rate revenue."""
    return creator_network.get_admin_metrics()

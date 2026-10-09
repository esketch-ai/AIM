"""AIM (AI Platform Initiative) - Consulting & Publishing API Router
(aim/api/consulting_router.py)
------------------------------------------------------------------
Exposes:
1. Real-time 4-pillar environmental infrastructure report
2. AI consulting prescriptive advice desk (4 actionable recipes)
3. One-click selection & multi-channel production content synthesis (Naver Place & Instagram)
4. Publication history ledger and live tracking
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aim.infra.marketing_infrastructure import MarketingInfrastructureEngine, ComprehensiveInfraReport
from aim.core.consulting_advisor import AIConsultingAdvisor, ConsultingDeskReport
from aim.core.publisher import ContentPublisher, FinalizedPublishingBundle, PublicationRecord


consulting_router = APIRouter(prefix="/api/v1/consulting", tags=["Consulting & Publishing"])


class SelectAndGenerateRequest(BaseModel):
    tenant_id: str = "TENANT_001"
    advice_id: str = "ADV_TENANT_001_WEATHER"


class MarkPublishedRequest(BaseModel):
    tenant_id: str = "TENANT_001"
    advice_id: Optional[str] = None
    channel: Optional[str] = None
    channels: Optional[List[str]] = None
    headline: Optional[str] = None
    trigger_type: Optional[str] = None
    gain_krw: Optional[int] = None


@consulting_router.get("/infrastructure-signals", response_model=ComprehensiveInfraReport, summary="4-Pillar Environmental Infra Intelligence")
def get_infrastructure_signals(location: str = "서울 성수동"):
    """Returns live weather, local geography, anniversary calendar and festival signals."""
    return MarketingInfrastructureEngine.build_infra_report(location)


@consulting_router.get("/prescriptions/{tenant_id}", response_model=ConsultingDeskReport, summary="AI Marketing Consultant Prescriptions")
def get_consulting_prescriptions(tenant_id: str):
    """Provides 4 actionable, high-ROI marketing prescriptions tailored to tenant's current infra context."""
    try:
        return AIConsultingAdvisor.evaluate_tenant(tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@consulting_router.post("/select-and-generate", response_model=FinalizedPublishingBundle, summary="Select Prescription & Generate Production Content")
def select_and_generate_content(req: SelectAndGenerateRequest):
    """Generates ready-to-publish content for Naver SmartPlace News and Instagram upon merchant choice."""
    try:
        return ContentPublisher.synthesize_bundle(req.tenant_id, req.advice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@consulting_router.get("/publishing-history/{tenant_id}", response_model=List[PublicationRecord], summary="Publication Ledger History")
def get_publishing_history(tenant_id: str):
    """Returns all publication records and live status for a tenant."""
    return ContentPublisher.get_history(tenant_id)


@consulting_router.post("/mark-published", response_model=PublicationRecord, summary="Record Publication Event")
def record_publication_event(req: MarkPublishedRequest):
    """Records that a merchant copied or published a campaign to Naver Place or Instagram."""
    ch = req.channel or (req.channels[0] if req.channels else "NAVER_PLACE")
    hd = req.headline or "[비 오는 날 3시간 한정] 갓 구운 바질소금빵 1+1 번개 혜택"
    tr = req.trigger_type or "🌧️ 마케팅 환경 인프라 감지"
    gn = req.gain_krw if req.gain_krw is not None else 240000

    return ContentPublisher.record_publication(
        tenant_id=req.tenant_id,
        channel=ch,
        headline=hd,
        trigger_type=tr,
        gain_krw=gn,
    )

"""AIM (AI Platform Initiative) - Revenue-Generating Business Command Center
FastAPI server serving:
1. Multi-Channel Content Generator (MZ, Worker, Family tones)
2. Real-Time Competitor Radar (1km Spy)
3. Flash Revenue Booster (Weather & Idle Table Fill)
4. Search Rank Doctor (Naver Place & ChatGPT 1st Place Booster)
5. 1-Star Reputation Crisis Defense
"""

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import json
import os

from aim.schema import RawStoreData, EvidenceTier
from aim.pipeline import AIMPipeline
from aim.normalizer import StoreDataNormalizer
from aim.generator import MultiChannelGenerator
from aim.url_ingester import StoreUrlIngester
from aim.reputation import ReputationCrisisEngine
from aim.intelligence import LocalIntelligenceEngine
from aim.testbed_engine import IndustryTestbedEngine
from aim.tenant.manager import TenantManager
from aim.tenant.approval import ApprovalDesk
from aim.admin.master_console import MasterAdminConsole
from aim.core.platform import AIMPlatform
from aim.admin.quarantine import ComplianceQuarantineQueue
from aim.tenant.billing import BillingService
from aim.api import service_router, tenant_router, admin_router, creator_router, orchestrator_router, monetization_router

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AIM Marketing OS", version="0.6.0")

# Mount Enterprise Decoupled Solution API Routers
app.include_router(service_router, prefix="/api/v1/service", tags=["Solution 1: Core Service Engine"])
app.include_router(tenant_router, prefix="/api/v1/tenant", tags=["Solution 2: Subscriber Tenant Portal"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Solution 3: Master Admin Control Plane"])
app.include_router(creator_router, tags=["Solution 4: Creator Marketplace & Escrow"])
app.include_router(orchestrator_router, tags=["Solution 5: Dynamic Organic Orchestrator"])
app.include_router(monetization_router, tags=["Solution 6: Multi-Channel Attribution & Monetization"])

# Mount Google Stitch Design Assets & Screen Gallery
DOCS_DESIGN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "design")
if os.path.exists(DOCS_DESIGN_DIR):
    app.mount("/docs/design", StaticFiles(directory=DOCS_DESIGN_DIR, html=True), name="stitch_design")


@app.get("/health")
def health_check():
    """Liveness probe returning platform health and operational status."""
    return {"status": "ok", "platform": "AIM Marketing OS", "version": "0.6.0"}


SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "sample_store.json"
)

LAST_PROFILE = None
testbed_engine = IndustryTestbedEngine()


class TenantCampaignExecuteRequest(BaseModel):
    tenant_id: str
    selected_channels: Optional[list[str]] = None


class UpdateTenantStatusRequest(BaseModel):
    tenant_id: str
    status: str


class UpdateTenantPlanRequest(BaseModel):
    tenant_id: str
    tier: str


class IngestUrlRequest(BaseModel):
    url: str
    tone: Optional[str] = "MZ_TREND"
    allow_mock_fallback: bool = Field(
        default=False,
        description="데모 모드 전용. True면 수집 실패 시 모의 데이터로 대체(운영 금지)",
    )


class ToneSwitchRequest(BaseModel):
    tone: str


class CrisisReviewRequest(BaseModel):
    store_name: str
    review_text: str
    rating: float = 1.0


class ApproveRequest(BaseModel):
    store_id: str
    selected_channels: list[str]


class SimulateTestbedRequest(BaseModel):
    industry_id: str
    custom_context: Optional[dict] = None


@app.get("/api/testbed/industries")
def list_testbed_industries():
    """Returns available industries in the testbed."""
    return {"industries": testbed_engine.list_industries()}


@app.get("/api/testbed/industry/{industry_id}")
def get_testbed_industry(industry_id: str):
    """Returns full 6D context and simulated actions for an industry."""
    profile = testbed_engine.get_industry(industry_id)
    if not profile:
        return JSONResponse(status_code=404, content={"error": "Industry not found"})
    return profile.model_dump()


@app.post("/api/testbed/simulate")
def simulate_testbed(req: SimulateTestbedRequest):
    """Executes dynamic 6D marketing action simulation with optional custom context."""
    try:
        profile = testbed_engine.simulate_action(req.industry_id, req.custom_context)
        return profile.model_dump()
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


# --- Subscriber Tenant Portal APIs ---

@app.get("/api/tenants")
def list_tenants():
    """Returns all subscriber tenant profiles for the workspace selector."""
    return {"tenants": [t.model_dump() for t in TenantManager.list_tenants()]}


@app.get("/api/tenant/{tenant_id}")
def get_tenant_dashboard(tenant_id: str):
    """Returns tenant account data and live orchestrated campaign plan."""
    tenant = TenantManager.get_tenant(tenant_id)
    if not tenant:
        return JSONResponse(status_code=404, content={"error": "Tenant not found"})

    plan = AIMPlatform.plan_campaign(tenant.business_state)
    return {
        "tenant": tenant.model_dump(),
        "live_plan": plan.model_dump(),
        "analytics": {
            "monthly_fee_krw": tenant.monthly_fee_krw,
            "cumulative_revenue_krw": tenant.cumulative_revenue_generated_krw,
            "roi_ratio": (
                round(tenant.cumulative_revenue_generated_krw / (tenant.monthly_fee_krw * 2), 1)
                if tenant.monthly_fee_krw > 0
                else 0.0
            ),
            "total_campaigns": tenant.total_campaigns_executed,
        },
    }


@app.post("/api/tenant/execute")
def execute_tenant_campaign(req: TenantCampaignExecuteRequest):
    """Executes campaign from the subscriber portal, attributing revenue to tenant account."""
    tenant = TenantManager.get_tenant(req.tenant_id)
    if not tenant:
        return JSONResponse(status_code=404, content={"error": "Tenant not found"})

    plan = AIMPlatform.plan_campaign(tenant.business_state)
    exec_result = AIMPlatform.execute_campaign(plan, req.selected_channels)
    TenantManager.record_campaign_execution(req.tenant_id, plan.strategy.projected_revenue)

    return {
        "status": "SUCCESS",
        "tenant_id": req.tenant_id,
        "business_name": tenant.business_name,
        "dispatched_channels": exec_result["dispatched_channels"],
        "projected_revenue": plan.strategy.projected_revenue,
        "evidence_tier": EvidenceTier.C_ILLUSTRATIVE.value,
        "projection_basis": (
            f"객단가 {tenant.business_state.unit_price:,}원 × 추정 {plan.strategy.projected_additional_units}건. "
            "유휴율·객단가는 실측 POS 정산 연동 전까지 시연값이므로 금전적 약속으로 사용하지 않습니다."
        ),
        "message": f"'{tenant.business_name}' 캠페인이 {len(exec_result['dispatched_channels'])}개 채널에 즉시 집행되었습니다.",
    }


@app.get("/api/tenant/{tenant_id}/staged-campaigns")
def get_tenant_staged_campaigns(tenant_id: str, status: Optional[str] = None):
    """Returns pending/staged campaigns for subscriber approval desk."""
    tenant = TenantManager.get_tenant(tenant_id)
    if not tenant:
        return JSONResponse(status_code=404, content={"error": f"Tenant '{tenant_id}' not found", "detail": f"Tenant '{tenant_id}' not found"})
    campaigns = ApprovalDesk.list_campaigns(tenant_id=tenant_id, status=status)
    return {"tenant_id": tenant_id, "campaigns": [c.model_dump() for c in campaigns]}


@app.post("/api/tenant/{tenant_id}/campaign/{campaign_id}/approve")
def approve_tenant_staged_campaign(tenant_id: str, campaign_id: str):
    """One-click mobile/portal approval of staged marketing campaign."""
    try:
        result = ApprovalDesk.approve_and_dispatch(campaign_id)
        return result
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e), "detail": str(e)})


@app.post("/api/tenant/{tenant_id}/campaign/{campaign_id}/reject")
def reject_tenant_staged_campaign(tenant_id: str, campaign_id: str):
    """Business owner rejection of staged campaign."""
    try:
        rejected = ApprovalDesk.reject_campaign(campaign_id, reason="Owner dismissed proposal")
        return {"status": "SUCCESS", "campaign": rejected.model_dump(), "message": "반려되었습니다"}
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e), "detail": str(e)})


# --- Platform Master Admin APIs ---

@app.get("/api/admin/overview")
def get_admin_overview():
    """Returns global platform KPIs, all tenant accounts, and compliance audit logs."""
    kpis = MasterAdminConsole.get_global_kpis()
    logs = MasterAdminConsole.get_audit_logs()
    tenants = TenantManager.list_tenants()
    return {
        "kpis": kpis.model_dump(),
        "tenants": [t.model_dump() for t in tenants],
        "audit_logs": [log.model_dump() for log in logs],
    }


@app.post("/api/admin/tenant/status")
def update_tenant_status(req: UpdateTenantStatusRequest):
    """Operator action to activate or pause tenant account."""
    updated = TenantManager.update_status(req.tenant_id, req.status)
    if not updated:
        return JSONResponse(status_code=404, content={"error": "Tenant not found"})
    return {"status": "SUCCESS", "tenant": updated.model_dump()}


@app.post("/api/admin/tenant/plan")
def update_tenant_plan(req: UpdateTenantPlanRequest):
    """Operator action to upgrade/downgrade tenant subscription tier."""
    updated = TenantManager.update_subscription_tier(req.tenant_id, req.tier)
    if not updated:
        return JSONResponse(status_code=404, content={"error": "Tenant not found"})
    return {"status": "SUCCESS", "tenant": updated.model_dump()}


@app.get("/api/current-package")
def get_current_package(tone: str = Query("MZ_TREND")):
    global LAST_PROFILE
    pipeline = AIMPipeline(SAMPLE_DATA_PATH)
    package = pipeline.run(tone=tone)

    with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
        raw_dict = json.load(f)
    LAST_PROFILE = StoreDataNormalizer.normalize(RawStoreData(**raw_dict))

    return package.model_dump()


@app.post("/api/switch-tone")
def switch_tone(req: ToneSwitchRequest):
    global LAST_PROFILE
    if LAST_PROFILE is None:
        pipeline = AIMPipeline(SAMPLE_DATA_PATH)
        with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
            raw_dict = json.load(f)
        LAST_PROFILE = StoreDataNormalizer.normalize(RawStoreData(**raw_dict))

    profile = LAST_PROFILE
    tone = req.tone

    blog = MultiChannelGenerator.generate_naver_blog(profile, tone=tone)
    insta = MultiChannelGenerator.generate_instagram(profile, tone=tone)
    kakao = MultiChannelGenerator.generate_kakaotalk(profile, tone=tone)

    return {
        "status": "success",
        "tone": tone,
        "store_profile": profile.model_dump(),
        "channels": {
            "naver_blog": blog.model_dump(),
            "instagram": insta.model_dump(),
            "kakaotalk": kakao.model_dump(),
        },
    }


@app.post("/api/ingest-url")
def ingest_url(req: IngestUrlRequest):
    global LAST_PROFILE
    raw_data, parsed_meta, is_live, provenance = StoreUrlIngester.ingest_url(
        req.url, allow_mock_fallback=req.allow_mock_fallback
    )

    # Gate 0: surface collection failure instead of generating content from mock data.
    if raw_data is None:
        return JSONResponse(
            status_code=502,
            content={
                "status": "COLLECTION_FAILED",
                "collection": provenance.model_dump(mode="json"),
                "message": "매장 정보를 불러오지 못했습니다. 네트워크를 확인하거나 아래의 직접 입력 경로를 이용해 주세요.",
                "fallback_hint": "네이버 플레이스·스마트스토어 URL을 직접 열어 기본 정보를 확인하거나, 정산 파일을 업로드해 주세요.",
            },
        )

    profile = StoreDataNormalizer.normalize(raw_data)
    LAST_PROFILE = profile

    tone = req.tone or "MZ_TREND"
    blog = MultiChannelGenerator.generate_naver_blog(profile, tone=tone)
    insta = MultiChannelGenerator.generate_instagram(profile, tone=tone)
    kakao = MultiChannelGenerator.generate_kakaotalk(profile, tone=tone)

    return {
        "status": "success",
        "is_live_crawled": is_live,
        "tone": tone,
        "collection": provenance.model_dump(mode="json"),
        "pos_evidence_tier": raw_data.pos_summary.evidence_tier.value,
        "parsed_metadata": parsed_meta,
        "store_profile": profile.model_dump(),
        "channels": {
            "naver_blog": blog.model_dump(),
            "instagram": insta.model_dump(),
            "kakaotalk": kakao.model_dump(),
        },
    }


@app.get("/api/intelligence")
def get_intelligence():
    """Returns real business intelligence: competitors, flash booster, and ranking diagnosis."""
    store_name = LAST_PROFILE.store_name if LAST_PROFILE else "성수 아뜰리에 베이커리 & 카페"
    competitors = LocalIntelligenceEngine.get_competitor_radar()
    booster = LocalIntelligenceEngine.generate_flash_booster(store_name)
    ranking = LocalIntelligenceEngine.diagnose_search_rank(store_name)

    return {
        "competitors": [c.model_dump() for c in competitors],
        "flash_booster": booster.model_dump(),
        "ranking_diagnosis": ranking.model_dump(),
    }


@app.post("/api/crisis-response")
def generate_crisis_response(req: CrisisReviewRequest):
    resp = ReputationCrisisEngine.generate_dignified_responses(
        store_name=req.store_name, review_text=req.review_text, rating=req.rating
    )
    return resp.model_dump()


@app.post("/api/approve")
def approve_campaign(req: ApproveRequest):
    return {
        "status": "APPROVED",
        "store_id": req.store_id,
        "message": f"성공적으로 {len(req.selected_channels)}개 채널에 즉각 집행되었습니다.",
        "scheduled_time": "실시간 타임어택 가동 (추가 매출은 POS 정산 실측 연동 후 산출됩니다)",
        "evidence_tier": EvidenceTier.C_ILLUSTRATIVE.value,
    }

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
INDEX_HTML_PATH = os.path.join(TEMPLATES_DIR, "index.html")


@app.get("/", response_class=HTMLResponse)
def index_page():
    if os.path.exists(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1>AIM Marketing OS</h1><div class='mobile-frame'>Template not found</div>"
    )

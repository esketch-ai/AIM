"""Tests for Marketing Infrastructure, AI Consulting Advisor, and Omni-Channel Publisher Flow
(tests/test_infrastructure_and_consulting_flow.py)
----------------------------------------------------------------------------------------
Validates:
1. 4-Pillar Environmental Marketing Infrastructure (Weather, Geography, Anniversary, Events)
2. Domain Conquest Strategy: 1st Flagship Local F&B Domain in-depth consulting
3. AI Consulting Advisor 4 Actionable Prescriptions (Weather, Events, Creator, Anniversary)
4. Omni-Channel Content Generation (Naver Place <=40 chars, Instagram, Creator 15s Storyboard, Kakao)
5. Publication History Ledger thread-safe recording & retrieval
6. Full FastAPI Consulting Router Endpoints via TestClient
7. Rendered HTML template verification of domain conquest banner and consulting desk
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from aim.web_app import app
from aim.tenant.manager import TenantManager
from aim.infra.marketing_infrastructure import (
    MarketingInfrastructureEngine,
    WeatherInfraSignal,
    LocalGeographySignal,
    AnniversarySignal,
    LocalEventSignal,
    ComprehensiveInfraReport,
    marketing_infra,
)
from aim.core.consulting_advisor import (
    AIConsultingAdvisor,
    PrescriptiveAdvice,
    ConsultingDeskReport,
    consulting_advisor,
)
from aim.core.publisher import (
    ContentPublisher,
    PublicationRecord,
    FinalizedPublishingBundle,
    content_publisher,
)

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. 4-Pillar Infrastructure Tests
# -----------------------------------------------------------------------------
def test_infrastructure_signals_full_report():
    """Validates that the 4-pillar environmental infrastructure service produces all signals."""
    report = MarketingInfrastructureEngine.build_infra_report("서울 성수동")
    assert report is not None
    assert isinstance(report, ComprehensiveInfraReport)

    # 1. Weather Signal
    weather = report.weather
    assert weather.location == "서울 성수동"
    assert weather.temperature_c > 0
    assert weather.precipitation_mm >= 0
    assert weather.condition_korean != ""
    assert weather.indoor_healing_demand_surge_pct > 0

    # 2. Geography Signal
    geo = report.geography
    assert "성수동" in geo.district_name
    assert geo.estimated_hourly_foot_traffic > 10000
    assert "2030 MZ" in geo.primary_demographics
    assert len(geo.nearby_anchors) >= 3

    # 3. Anniversary Signal
    anniv = report.active_anniversary
    assert anniv.name != ""
    assert anniv.d_day >= 0
    assert isinstance(report.upcoming_anniversaries, list)
    assert len(report.upcoming_anniversaries) >= 3

    # 4. Local Event Signal
    events = report.active_local_events
    assert isinstance(events, list)
    assert len(events) >= 1
    assert events[0].expected_foot_traffic_surge_pct > 0


def test_anniversary_golden_time_logic():
    """Validates anniversary D-Day calculation and golden time threshold (<=7 days)."""
    # Test with March 10 (White Day is March 14, D-4)
    ref_date_golden = date(2026, 3, 10)
    active, upcoming = MarketingInfrastructureEngine.get_anniversaries_infra(ref_date_golden)
    assert active.name == "화이트데이"
    assert active.d_day == 4
    assert active.is_golden_time is True
    assert "골든타임" in active.urgency_tag

    # Test with March 1 (White Day is March 14, D-13)
    ref_date_early = date(2026, 3, 1)
    active_early, upcoming_early = MarketingInfrastructureEngine.get_anniversaries_infra(ref_date_early)
    assert active_early.name == "화이트데이"
    assert active_early.d_day == 13
    assert active_early.is_golden_time is True  # 13 <= 14 days
    assert "기획 추천" in active_early.urgency_tag


def test_geography_and_events_by_location():
    """Validates location-specific geography and local events lookup."""
    seongsu_geo = MarketingInfrastructureEngine.get_geography_infra("서울 성수동")
    assert "성수" in seongsu_geo.district_name

    gangnam_geo = MarketingInfrastructureEngine.get_geography_infra("서울 강남역")
    assert "강남" in gangnam_geo.district_name

    seongsu_events = MarketingInfrastructureEngine.get_local_events_infra("서울 성수동")
    assert any("성수" in e.location or "서울숲" in e.location for e in seongsu_events)


# -----------------------------------------------------------------------------
# 2. Domain Conquest Strategy & AI Consulting Advisor Tests
# -----------------------------------------------------------------------------
def test_consulting_advisor_flagship_fnb_prescriptions():
    """Validates that F&B flagship domain receives 4 high-value consulting prescriptions."""
    tenant = TenantManager.get_tenant("TENANT_001")
    assert tenant is not None
    assert tenant.domain == "fnb"

    report = AIConsultingAdvisor.evaluate_tenant("TENANT_001")
    assert isinstance(report, ConsultingDeskReport)
    assert len(report.prescriptions) == 4

    categories = [p.category for p in report.prescriptions]
    assert "WEATHER_SALVAGE" in categories
    assert "LOCAL_EVENT_SURGE" in categories
    assert "CREATOR_COLLAB" in categories
    assert "ANNIVERSARY_EARLY" in categories

    for p in report.prescriptions:
        assert p.expected_revenue_gain_krw > 0
        assert p.expected_roi_ratio >= 1.0
        assert len(p.headline) > 10
        assert len(p.diagnosis) > 20
        assert len(p.recommended_action) > 20
        assert p.urgency_badge != ""


def test_consulting_advisor_tenant_evaluation_consistency():
    """Validates that consulting advisor produces customized recommendations for tenants."""
    report = AIConsultingAdvisor.evaluate_tenant("TENANT_001")
    assert report.tenant_id == "TENANT_001"
    assert "성수 아뜰리에" in report.business_name
    assert "수석 마케팅 컨설턴트" in report.consultant_summary


# -----------------------------------------------------------------------------
# 3. Omni-Channel Content Generation & Compliance Tests
# -----------------------------------------------------------------------------
def test_naver_place_strict_spec_compliance():
    """Validates that Naver Place News title strictly respects the 40-character limit constraint."""
    bundle = ContentPublisher.synthesize_bundle("TENANT_001", "ADV_TENANT_001_WEATHER")
    naver = bundle.naver_place
    assert len(naver.title_max40) <= 40, f"Naver Place headline exceeded 40 chars: '{naver.title_max40}' ({len(naver.title_max40)} chars)"
    assert len(naver.body_text) > 30
    assert "AIM-" in naver.coupon_link_code
    assert "쿠폰" in naver.body_text
    assert "1080x1080" in naver.image_asset_spec
    assert "【네이버 플레이스" in naver.clipboard_text


def test_instagram_and_creator_pitch_content_generation():
    """Validates Instagram caption hashtags and Creator 15s Storyboard pitch."""
    bundle = ContentPublisher.synthesize_bundle("TENANT_001", "ADV_TENANT_001_EVENT")

    # Instagram
    insta = bundle.instagram
    assert len(insta.caption_body) > 30
    assert len(insta.hooking_first_line) > 5
    assert len(insta.hashtags) >= 6
    assert any(h.startswith("#") for h in insta.hashtags)

    # Creator Pitch
    creator = bundle.creator_pitch
    assert creator.matched_creator_name != ""
    assert creator.matched_creator_handle.startswith("@")
    assert "hook_0_3s" in creator.storyboard_15s
    assert "body_3_10s" in creator.storyboard_15s
    assert "cta_10_15s" in creator.storyboard_15s
    assert creator.escrow_fee_krw > 0
    assert "에스크로" in creator.proposal_message_text


# -----------------------------------------------------------------------------
# 4. Publication History Ledger Tests
# -----------------------------------------------------------------------------
def test_publication_history_ledger_operations():
    """Validates recording, sorting, and tenant filtering in the publication ledger."""
    initial_records = ContentPublisher.get_history("TENANT_001")
    initial_count = len(initial_records)

    new_record = ContentPublisher.record_publication(
        tenant_id="TENANT_001",
        channel="NAVER_PLACE",
        headline="[단위테스트 소식] 성수동 소금빵 갓 구움",
        trigger_type="단위테스트 기상 감지",
        gain_krw=300000,
    )

    assert new_record.record_id.startswith("PUB_REC_")
    updated_records = ContentPublisher.get_history("TENANT_001")
    assert len(updated_records) == initial_count + 1
    assert updated_records[0].record_id == new_record.record_id
    assert updated_records[0].headline == "[단위테스트 소식] 성수동 소금빵 갓 구움"


# -----------------------------------------------------------------------------
# 5. FastAPI Endpoints Integration Tests (TestClient)
# -----------------------------------------------------------------------------
def test_consulting_api_infrastructure_signals():
    """GET /api/v1/consulting/infrastructure-signals returns valid infrastructure telemetry."""
    res = client.get("/api/v1/consulting/infrastructure-signals")
    assert res.status_code == 200
    data = res.json()
    assert "weather" in data
    assert "geography" in data
    assert "active_anniversary" in data
    assert "active_local_events" in data


def test_consulting_api_prescriptions_flow():
    """GET /api/v1/consulting/prescriptions/{tenant_id} returns prescriptions list."""
    res = client.get("/api/v1/consulting/prescriptions/TENANT_001")
    assert res.status_code == 200
    data = res.json()
    assert "prescriptions" in data
    assert len(data["prescriptions"]) >= 4
    first_advice = data["prescriptions"][0]
    assert "advice_id" in first_advice
    assert first_advice["expected_revenue_gain_krw"] > 0


def test_consulting_api_select_and_generate_flow():
    """POST /api/v1/consulting/select-and-generate generates full omni-channel bundle."""
    payload = {
        "tenant_id": "TENANT_001",
        "advice_id": "ADV_TENANT_001_WEATHER"
    }
    res = client.post("/api/v1/consulting/select-and-generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "naver_place" in data
    assert "instagram" in data
    assert "creator_pitch" in data
    assert "kakao_channel" in data
    assert len(data["naver_place"]["title_max40"]) <= 40


def test_consulting_api_mark_published_and_history():
    """POST /api/v1/consulting/mark-published records into ledger and appears in history."""
    publish_payload = {
        "tenant_id": "TENANT_001",
        "advice_id": "ADV_TENANT_001_EVENT",
        "channel": "NAVER_PLACE",
        "headline": "[비 오는 날 3시간 한정] 갓 구운 바질소금빵 1+1 번개 혜택"
    }
    pub_res = client.post("/api/v1/consulting/mark-published", json=publish_payload)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "LIVE"
    assert pub_data["record_id"].startswith("PUB_REC_")
    assert pub_data["tenant_id"] == "TENANT_001"

    # Verify history endpoint
    hist_res = client.get("/api/v1/consulting/publishing-history/TENANT_001")
    assert hist_res.status_code == 200
    history_list = hist_res.json()
    assert len(history_list) >= 2


# -----------------------------------------------------------------------------
# 6. Rendered HTML Verification (UI Grounding)
# -----------------------------------------------------------------------------
def test_rendered_html_consulting_desk_and_domain_conquest():
    """Validates that rendered index.html contains all user-requested infrastructure and consulting UI elements."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Domain Conquest Strategy Banner
    assert "[도메인 정복 전략] 1차 플래그십:" in html
    assert "로컬 F&B 외식·카페" in html
    assert "플래그십 가동 중" in html

    # 2. 4-Pillar Infrastructure Sensing Bar
    assert "4대 마케팅 환경 인프라 실시간 센싱" in html
    assert "infraWeatherCard" in html
    assert "infraGeoCard" in html
    assert "infraAnnivCard" in html
    assert "infraEventCard" in html

    # 3. AI Marketing Consulting Prescriptions Desk
    assert "AI MARKETING CONSULTING DESK" in html
    assert "매출 부진 시 수백만원 컨설팅비 대신, AI가 실시간 무료 처방을 내립니다" in html
    assert "consultingPrescriptionsGrid" in html

    # 4. Publication History Ledger
    assert "PUBLICATION & CHANNEL MANAGEMENT LEDGER" in html
    assert "실시간 발행 및 채널 관리 히스토리 원장" in html
    assert "publicationHistoryList" in html

    # 5. Omni-Channel Publishing Modal
    assert "publishingModal" in html
    assert "pubTabBtn_naver" in html
    assert "pubTabBtn_instagram" in html
    assert "pubTabBtn_creator" in html
    assert "pubTabBtn_kakao" in html
    assert "pubNaverTitle" in html

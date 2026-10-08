"""
Test Suite for AIM Organic Dynamic Orchestrator & Value Attribution
Tests:
1. DynamicTriggerSignal processing across 5 signal types (Weather, Competitor, Rank, Crisis, POS)
2. Closed-loop OrchestratedActionBundle creation (Value compression + Brief + Creators + Escrow + Projected ROI)
3. ValueAttributionLedger accounting & Gate 0 evidence tier compliance
4. End-to-end REST API endpoints in orchestrator_router
"""

import pytest
from fastapi.testclient import TestClient

from aim.core.dynamic_orchestrator import (
    DynamicOrchestrator,
    DynamicTriggerSignal,
)
from aim.core.value_attribution import ValueAttributionLedger
from aim.web_app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_weather_idle_signal_orchestration():
    orchestrator = DynamicOrchestrator()
    signal = DynamicTriggerSignal(
        signal_id="SIG_WEATHER_01",
        tenant_id="TENANT_001",
        signal_type="WEATHER_IDLE",
        headline="오늘 15시 비 예보 + 2시 이후 조기 품절",
        detected_data={"rain_prob": 80, "idle_rate": 35},
    )

    bundle = orchestrator.process_signal(signal, subscriber_plan="PRO")

    assert bundle.bundle_id.startswith("BUNDLE_")
    assert bundle.tenant_id == "TENANT_001"
    assert bundle.domain == "FNB"
    assert "비 예보" in bundle.strategy_summary
    assert "비 오는 날" in bundle.omnichannel_copies["kakao_alert"]["headline"]
    assert "나른한 오후" in bundle.compressed_pitch["pain_point_strike"]
    assert len(bundle.creator_brief["scenes"]) == 4
    assert len(bundle.matched_creators) == 3
    assert bundle.escrow_preview["take_rate_pct"] == 10.0
    assert bundle.escrow_preview["subscriber_discount_applied"] is True
    assert bundle.projected_revenue_krw == 240000
    assert bundle.projected_roi > 0.0
    assert bundle.evidence_tier == "C_ILLUSTRATIVE"


def test_competitor_weakness_signal_orchestration():
    orchestrator = DynamicOrchestrator()
    signal = DynamicTriggerSignal(
        signal_id="SIG_COMP_01",
        tenant_id="TENANT_001",
        signal_type="COMPETITOR_WEAKNESS",
        headline="B카페 쿠키 너무 달고 좌석 좁다는 고객 불만 3건 포착",
        detected_data={"competitor": "B카페", "distance": "250m"},
    )

    bundle = orchestrator.process_signal(signal, subscriber_plan="PRO")

    assert "반사이익" in bundle.strategy_summary
    assert "B카페" in bundle.omnichannel_copies["kakao_alert"]["body"]
    assert bundle.projected_revenue_krw == 360000


def test_rank_drop_and_crisis_signals():
    orchestrator = DynamicOrchestrator()

    # 1. Rank Drop
    rank_sig = DynamicTriggerSignal(
        signal_id="SIG_RANK_01",
        tenant_id="TENANT_001",
        signal_type="RANK_DROP",
        headline="네이버 플레이스 4위 진단: 키워드 부족",
    )
    b_rank = orchestrator.process_signal(rank_sig)
    assert "1위로 도약" in b_rank.strategy_summary
    assert "영수증 리뷰" in b_rank.strategy_summary

    # 2. Crisis Review
    crisis_sig = DynamicTriggerSignal(
        signal_id="SIG_CRISIS_01",
        tenant_id="TENANT_001",
        signal_type="CRISIS_REVIEW",
        headline="별점 1점 악성 리뷰 인입: 대기 길고 조기 품절",
    )
    b_crisis = orchestrator.process_signal(crisis_sig)
    assert "품격 대응" in b_crisis.strategy_summary


def test_value_attribution_ledger_accounting():
    ledger = ValueAttributionLedger()
    entry = ledger.record_attribution(
        tenant_id="TENANT_001",
        source_type="CAMPAIGN_DISPATCH",
        title="가을비 타임어택",
        units_generated=10,
        unit_price=24000,
        cost_incurred_krw=0,
    )

    assert entry.gross_revenue_krw == 240000
    assert entry.evidence_tier == "C_ILLUSTRATIVE"

    summary = ledger.get_tenant_summary("TENANT_001", monthly_fee_krw=49000, business_name="성수 베이커리")
    assert summary.cumulative_revenue_krw >= 2320000
    assert summary.roi_multiplier > 0.0
    assert summary.evidence_tier == "C_ILLUSTRATIVE"


def test_orchestrator_api_lifecycle(client):
    # 1. POST /api/v1/orchestrator/trigger
    trig_resp = client.post(
        "/api/v1/orchestrator/trigger",
        json={
            "signal_id": "SIG_API_01",
            "tenant_id": "TENANT_001",
            "signal_type": "WEATHER_IDLE",
            "headline": "15시 비 예보",
            "detected_data": {"rain_prob": 80},
        },
    )
    assert trig_resp.status_code == 200
    bundle_data = trig_resp.json()
    assert bundle_data["bundle_id"].startswith("BUNDLE_")
    bundle_id = bundle_data["bundle_id"]

    # 2. GET /api/v1/orchestrator/live-stream/TENANT_001
    stream_resp = client.get("/api/v1/orchestrator/live-stream/TENANT_001")
    assert stream_resp.status_code == 200
    assert stream_resp.json()["bundle_count"] >= 1

    # 3. POST /api/v1/orchestrator/execute-bundle
    exec_resp = client.post(
        "/api/v1/orchestrator/execute-bundle",
        json={
            "bundle_id": bundle_id,
            "tenant_id": "TENANT_001",
            "selected_channels": ["blog", "instagram", "kakaotalk"],
            "order_creator_escrow": True,
        },
    )
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["status"] == "SUCCESS"
    assert exec_data["projected_revenue_krw"] > 0
    assert exec_data["escrow_deal"]["status"] == "ESCROW_LOCKED"

    # 4. GET /api/v1/orchestrator/global-flow
    flow_resp = client.get("/api/v1/orchestrator/global-flow")
    assert flow_resp.status_code == 200
    flow_data = flow_resp.json()
    assert flow_data["total_signals_orchestrated"] >= 1
    assert "pipeline_health" in flow_data

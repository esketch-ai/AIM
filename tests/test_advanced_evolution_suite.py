"""AIM (AI Platform Initiative) - Advanced Evolution Unit Test Suite
tests/test_advanced_evolution_suite.py
-------------------------------------------------------------------
Granular verification of 5 result-driven advanced evolutionary subsystems:
1. Dynamic 3-tier scenario modeling & BEP payback days engine
2. Merchant rejection feedback learning & A/B variant copy engine
3. Creator 24h Fast-Track review, 1-revision limit & milestone bonus unlock
4. Cross-attribution multi-touch deduplication & monthly statement generation
5. Guardian radar anomaly circuit breaker & peer benchmark ranking
6. REST API contracts for all evolution endpoints
"""

import pytest
from fastapi.testclient import TestClient

from aim.core.scenario_engine import ScenarioEngine, ScenarioResult
from aim.core.feedback_learner import FeedbackLearner
from aim.core.cross_attribution import CrossAttributionEngine
from aim.matching.creator_network import creator_network
from aim.tenant.approval import ApprovalDesk
from aim.tenant.manager import TenantManager
from aim.admin.master_console import MasterAdminConsole
from aim.web_app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_evolution_state():
    """Resets all in-memory evolution singletons before each test."""
    TenantManager._tenants.clear()
    TenantManager._initialize_defaults()
    ApprovalDesk._staged_campaigns.clear()
    ApprovalDesk._initialize_defaults()
    FeedbackLearner._tenant_constraints.clear()
    FeedbackLearner._campaign_variants.clear()
    MasterAdminConsole._circuit_breakers.clear()
    creator_network.active_deals.clear()
    creator_network._initialize_defaults()
    yield


# ============================================================================
# 1. Dynamic 3-Tier Scenario & BEP Payback Tests
# ============================================================================
class TestDynamicScenarioAndBEP:
    """Verifies math, downside risk protection, upside viral peak, and payback days."""

    def test_fnb_bakery_3tier_scenarios(self):
        res = ScenarioEngine.calculate_scenarios("FNB", 25000000, 49000)
        assert isinstance(res, ScenarioResult)
        assert res.category == "FNB"
        assert res.monthly_revenue_krw == 25000000

        scenarios = res.scenarios
        assert "downside" in scenarios
        assert "baseline" in scenarios
        assert "upside" in scenarios

        # Baseline = 25M * 0.17 = 4,250,000 KRW
        assert scenarios["baseline"].monthly_gain_krw == 4250000
        assert scenarios["baseline"].roi_multiplier == pytest.approx(86.7, abs=0.1)

        # Downside = 65% of baseline = 2,762,500 KRW
        assert scenarios["downside"].monthly_gain_krw == 2762500
        assert scenarios["downside"].roi_multiplier == pytest.approx(56.4, abs=0.1)

        # Upside = 185% of baseline = 7,862,500 KRW
        assert scenarios["upside"].monthly_gain_krw == 7862500
        assert scenarios["upside"].roi_multiplier == pytest.approx(160.5, abs=0.1)

        # Payback period: daily gain = 4,250,000 / 30 = 141,666 KRW; 49,000 / 141,666 = ~0.3 days
        assert res.payback_days <= 1.0

    def test_medical_clinic_3tier_scenarios_and_hours(self):
        res = ScenarioEngine.calculate_scenarios("MEDICAL", 50000000, 49000)
        assert res.scenarios["baseline"].monthly_gain_krw == 7500000
        assert res.scenarios["upside"].monthly_gain_krw > 13000000
        assert res.scenarios["downside"].hours_saved >= 12
        assert res.payback_days < 0.5

    def test_manufacturing_and_saas_scenarios(self):
        saas_res = ScenarioEngine.calculate_scenarios("SAAS", 30000000, 49000)
        mfg_res = ScenarioEngine.calculate_scenarios("MANUFACTURING", 80000000, 49000)
        assert saas_res.scenarios["baseline"].monthly_gain_krw == 6600000
        assert mfg_res.scenarios["baseline"].monthly_gain_krw == 16000000
        assert mfg_res.payback_days <= 0.1


# ============================================================================
# 2. Feedback Learning & A/B Copy Variant Tests
# ============================================================================
class TestFeedbackLearningAndABVariants:
    """Verifies adaptive rejection feedback storage and A/B variant copy mechanics."""

    def test_record_discount_too_high_feedback(self):
        c = FeedbackLearner.record_feedback(
            tenant_id="TENANT_001",
            reason_code="DISCOUNT_TOO_HIGH",
            note="원가 마진 때문에 10% 이상 할인은 곤란합니다",
        )
        assert c.reason_code == "DISCOUNT_TOO_HIGH"
        assert "10% 이내" in c.applied_rule

        constraints = FeedbackLearner.get_tenant_constraints("TENANT_001")
        assert len(constraints) == 1
        assert constraints[0].applied_rule == c.applied_rule

    def test_record_tone_and_audience_feedback(self):
        FeedbackLearner.record_feedback("TENANT_002", "TONE_TOO_CASUAL", "의원 격에 맞게 존댓말 유지 요망")
        FeedbackLearner.record_feedback("TENANT_002", "WRONG_AUDIENCE", "3040 오피스 직장인 대상")

        modifiers = FeedbackLearner.get_active_prompt_modifiers("TENANT_002")
        assert len(modifiers) == 2
        assert any("정중" in m for m in modifiers)
        assert any("3040" in m for m in modifiers)

    def test_ab_variant_copy_generation_and_ctr(self):
        variants = FeedbackLearner.generate_ab_variants(
            campaign_id="CAMP-001",
            tenant_id="TENANT_001",
            base_title="가을비 타임어택 사워도우",
            base_body="갓 구운 천연발효 사워도우 1+1",
        )
        assert variants.campaign_id == "CAMP-001"
        assert variants.variant_a.strategy_theme == "BENEFIT_CURIOSITY"
        assert variants.variant_b.strategy_theme == "URGENCY_SCARCITY"
        assert variants.variant_a.ctr_percent > 0
        assert variants.variant_b.ctr_percent > 0
        assert variants.winner_variant_id in ["VARIANT_A", "VARIANT_B"]

    def test_approval_desk_reject_with_feedback_integration(self):
        res = ApprovalDesk.reject_with_feedback(
            campaign_id="CAMP-001",
            reason_code="TONE_TOO_CASUAL",
            note="너무 장난스러운 문구 지양",
        )
        assert res["status"] == "REJECTED"
        assert "자율 학습 규칙" in res["message"]
        camp = ApprovalDesk.get_campaign("CAMP-001")
        assert camp.status == "REJECTED"


# ============================================================================
# 3. Creator 24h Fast-Track & Milestone Bonus Tests
# ============================================================================
class TestCreatorFastTrackAndMilestoneBonus:
    """Verifies draft submission, single revision limit, base payout & milestone bonus."""

    def test_submit_creator_draft_success(self):
        deal = creator_network.create_escrow_deal(
            tenant_id="TENANT_001", creator_id="CR_FNB_02", brief_id="BRIEF_01", subscriber_plan="PRO"
        )
        res = creator_network.submit_draft(deal.deal_id, "https://cdn.aim.link/v/shorts_01.mp4", True)
        assert res["status"] == "DRAFT_SUBMITTED"
        assert res["compliance_checked"] is True
        assert res["fast_track_hours_left"] == 24

    def test_single_point_revision_limit_enforced(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        creator_network.submit_draft(deal.deal_id, "https://cdn.aim.link/v/shorts_01.mp4")

        # 1st revision request: allowed
        d1 = creator_network.request_revision(deal.deal_id, "마지막 장면 로고 0.5초 더 길게")
        assert d1.revision_count == 1
        assert d1.status == "REVISION_REQUESTED"

        # 2nd revision request: must raise ValueError under Fast-Track SLA
        with pytest.raises(ValueError, match="1회를 초과하는 수정 요청은 불가합니다"):
            creator_network.request_revision(deal.deal_id, "한 번 더 수정해주세요")

    def test_approve_draft_releases_base_payout_70_percent(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        res = creator_network.approve_draft_and_release_base(deal.deal_id)
        assert res["status"] == "BASE_PAYOUT_RELEASED"
        assert res["released_base_payout_krw"] == deal.creator_base_payout
        assert res["held_bonus_payout_krw"] == deal.creator_bonus_payout
        assert deal.status == "BASE_PAYOUT_RELEASED"

    def test_unlock_milestone_bonus_30_percent_success_and_failure(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        creator_network.approve_draft_and_release_base(deal.deal_id)

        # Failure when views < 50,000
        with pytest.raises(ValueError, match="성과 마일스톤 기준 미달"):
            creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="VIEWS", metric_value=24000)

        # Success when views >= 50,000
        res = creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="VIEWS", metric_value=62000)
        assert res["status"] == "SETTLED"
        assert res["unlocked_bonus_krw"] == deal.creator_bonus_payout
        assert deal.status == "SETTLED"


# ============================================================================
# 4. Cross-Attribution Deduplication & Monthly Statement Tests
# ============================================================================
class TestCrossAttributionAndSettlement:
    """Verifies multi-touch deduplication, Shapley weights, and monthly statement."""

    def test_deduplicate_transaction_multi_touch(self):
        channels = ["UTM_SHORTS", "KAKAO_ALERT", "POS_COUPON"]
        res = CrossAttributionEngine.deduplicate_transaction(
            tenant_id="TENANT_001",
            customer_id="CUST_8841",
            order_amount_krw=30000,
            channels=channels,
        )
        # Raw claim was 30,000 * 3 = 90,000; actual order is 30,000
        assert res.actual_order_amount_krw == 30000
        assert res.raw_claimed_total_krw == 90000
        assert res.deduplication_saved_krw == 60000
        assert len(res.touchpoints) == 3

        # Weights sum to 1.0 (approx)
        total_weight = sum(t.shapley_weight for t in res.touchpoints)
        assert total_weight == pytest.approx(1.0, abs=0.01)

        # Total attributed sum equals order amount (within 1 KRW rounding)
        total_attr = sum(t.attributed_amount_krw for t in res.touchpoints)
        assert abs(total_attr - 30000) <= 2

        # 8% platform fee (2,400), 3% creator bonus (900), 89% merchant (26,700)
        assert res.revenue_split["platform_fee_krw"] == 2400
        assert res.revenue_split["creator_bonus_krw"] == 900
        assert res.revenue_split["merchant_net_revenue_krw"] == 26700

    def test_generate_monthly_settlement_statement(self):
        stmt = CrossAttributionEngine.generate_monthly_statement(
            tenant_id="TENANT_001",
            business_name="성수 아뜰리에 베이커리 & 카페",
            cumulative_gmv=5000000,
            monthly_fee=49000,
        )
        assert stmt.total_attributed_gmv_krw == 5000000
        assert stmt.platform_take_rate_krw == 400000  # 8%
        assert stmt.creator_performance_bonus_krw == 150000  # 3%
        assert stmt.merchant_net_revenue_krw == 4450000  # 89%
        assert stmt.saas_subscription_fee_krw == 49000
        assert stmt.net_payout_to_merchant_krw == 4450000 - 49000
        assert stmt.roi_multiple >= 50.0


# ============================================================================
# 5. Circuit Breaker & Peer Benchmark Tests
# ============================================================================
class TestCircuitBreakerAndPeerBenchmark:
    """Verifies fraud anomaly detection, circuit breaker tripping, and peer benchmark."""

    def test_circuit_breaker_duplicate_receipt_anomaly(self):
        rec = MasterAdminConsole.scan_and_trip_circuit_breaker(
            tenant_id="TENANT_001",
            anomaly_type="DUPLICATE_RECEIPT_FRAUD",
            evidence_payload={"receipt_no": "REC-8841", "attempt_count": 2},
        )
        assert rec["anomaly_type"] == "DUPLICATE_RECEIPT_FRAUD"
        assert rec["status"] == "TRIPPED_FROZEN"
        assert "동일 영수증 번호 2차 등록 즉시 동결" in rec["defense_action"]

        status = MasterAdminConsole.get_circuit_breaker_status()
        assert status["health"] == "CIRCUIT_TRIPPED_ACTIVE"
        assert status["currently_frozen_count"] == 1

    def test_circuit_breaker_rapid_coupon_burst(self):
        rec = MasterAdminConsole.scan_and_trip_circuit_breaker(
            tenant_id="TENANT_001",
            anomaly_type="RAPID_COUPON_BURST",
            evidence_payload={"scans_per_minute": 18, "coupon": "AIM-RAIN24K"},
        )
        assert rec["anomaly_type"] == "RAPID_COUPON_BURST"
        assert rec["status"] == "TRIPPED_FROZEN"

    def test_peer_benchmark_fnb_tenant_001(self):
        bench = MasterAdminConsole.get_peer_benchmark("TENANT_001")
        assert bench["tenant_id"] == "TENANT_001"
        assert bench["domain"] == "fnb"
        assert bench["peers_analyzed_count"] == 28
        assert bench["percentile_score"] >= 80.0
        assert "우수" in bench["rank_label"]
        assert bench["growth_rate_vs_peers"] > 0

    def test_peer_benchmark_invalid_tenant_raises(self):
        with pytest.raises(ValueError, match="Tenant INVALID_ID not found"):
            MasterAdminConsole.get_peer_benchmark("INVALID_ID")


# ============================================================================
# 6. REST API Contracts for Evolution Endpoints
# ============================================================================
class TestEvolutionRestApiContracts:
    """Verifies all FastAPI routes exposed for advanced evolution features."""

    def test_api_scenario_calculate(self, client):
        r = client.post(
            "/api/v1/scenario/calculate",
            json={"category": "BEAUTY", "revenue": 20000000, "monthly_fee": 49000},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["category"] == "BEAUTY"
        assert "scenarios" in data
        assert data["payback_days"] > 0

    def test_api_reject_with_feedback(self, client):
        r = client.post(
            "/api/v1/tenant/campaign/CAMP-001/reject-with-feedback",
            json={"reason_code": "WRONG_AUDIENCE", "note": "젊은 층보다 30대 위주로"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "REJECTED"
        assert data["feedback_recorded"]["reason_code"] == "WRONG_AUDIENCE"

    def test_api_campaign_variants(self, client):
        r = client.get("/api/v1/tenant/campaign/CAMP-001/variants?tenant_id=TENANT_001")
        assert r.status_code == 200
        data = r.json()
        assert "variant_a" in data
        assert "variant_b" in data
        assert data["variant_a"]["strategy_theme"] == "BENEFIT_CURIOSITY"

    def test_api_creator_draft_workflow_and_bonus(self, client):
        # 1. Submit Draft
        r1 = client.post(
            "/api/v1/creator/deal/DEAL_7749A/draft/submit",
            json={"video_url": "https://cdn.aim.link/v15.mp4", "compliance_passed": True},
        )
        assert r1.status_code == 200
        assert r1.json()["status"] == "DRAFT_SUBMITTED"

        # 2. Approve Draft
        r2 = client.post("/api/v1/creator/deal/DEAL_7749A/draft/approve")
        assert r2.status_code == 200
        assert r2.json()["status"] == "BASE_PAYOUT_RELEASED"

        # 3. Unlock Milestone Bonus
        r3 = client.post(
            "/api/v1/creator/deal/DEAL_7749A/milestone/unlock",
            json={"metric_type": "VIEWS", "metric_value": 75000},
        )
        assert r3.status_code == 200
        assert r3.json()["status"] == "SETTLED"

    def test_api_creator_revision_limit(self, client):
        # 1st revision request
        r1 = client.post(
            "/api/v1/creator/deal/DEAL_7749A/draft/revision",
            json={"feedback": "첫 화면 폰트 크기 확대"},
        )
        assert r1.status_code == 200

        # 2nd revision request: should return 400
        r2 = client.post(
            "/api/v1/creator/deal/DEAL_7749A/draft/revision",
            json={"feedback": "다시 한번 수정"},
        )
        assert r2.status_code == 400
        assert "1회를 초과하는 수정" in r2.json()["error"]

    def test_api_attribution_deduplicate(self, client):
        r = client.post(
            "/api/v1/attribution/deduplicate",
            json={
                "tenant_id": "TENANT_001",
                "customer_id": "CUST_9912",
                "order_amount_krw": 40000,
                "channels": ["UTM_SHORTS", "POS_COUPON"],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["actual_order_amount_krw"] == 40000
        assert data["deduplication_saved_krw"] == 40000
        assert len(data["touchpoints"]) == 2

    def test_api_attribution_monthly_statement(self, client):
        r = client.get("/api/v1/attribution/monthly-statement/TENANT_001")
        assert r.status_code == 200
        data = r.json()
        assert data["tenant_id"] == "TENANT_001"
        assert "billing_period" in data
        assert data["merchant_net_revenue_krw"] > 0
        assert data["platform_take_rate_krw"] > 0

    def test_api_circuit_breaker_status_and_simulate(self, client):
        # Status
        r1 = client.get("/api/v1/admin/circuit-breaker/status")
        assert r1.status_code == 200

        # Simulate anomaly
        r2 = client.post(
            "/api/v1/admin/circuit-breaker/simulate-anomaly",
            json={
                "tenant_id": "TENANT_001",
                "anomaly_type": "DUPLICATE_RECEIPT_FRAUD",
                "evidence": {"receipt_no": "REC-999"},
            },
        )
        assert r2.status_code == 200
        assert r2.json()["circuit_breaker"]["status"] == "TRIPPED_FROZEN"

    def test_api_peer_benchmark(self, client):
        r = client.get("/api/v1/admin/fleet/benchmark/TENANT_001")
        assert r.status_code == 200
        data = r.json()
        assert data["tenant_id"] == "TENANT_001"
        assert "percentile_score" in data
        assert "rank_label" in data

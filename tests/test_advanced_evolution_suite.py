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

    def test_zero_revenue_scenario(self):
        res = ScenarioEngine.calculate_scenarios("FNB", 0, 49000)
        assert res.monthly_revenue_krw == 0
        assert res.scenarios["baseline"].monthly_gain_krw == 0
        assert res.scenarios["baseline"].roi_multiplier == 0.0
        assert res.payback_days == 0.0

    def test_negative_revenue_normalized(self):
        res = ScenarioEngine.calculate_scenarios("FNB", -500000, 49000)
        assert res.monthly_revenue_krw == 0
        assert res.scenarios["baseline"].monthly_gain_krw == 0

    def test_zero_monthly_fee_free_tier(self):
        res = ScenarioEngine.calculate_scenarios("FNB", 20000000, 0)
        assert res.monthly_subscription_fee_krw == 0
        assert res.scenarios["baseline"].roi_multiplier == 0.0
        assert res.payback_days == 0.0

    def test_enterprise_tier_fee_payback(self):
        res = ScenarioEngine.calculate_scenarios("MEDICAL", 50000000, 199000)
        assert res.monthly_subscription_fee_krw == 199000
        # Daily gain = 7,500,000 / 30 = 250,000 KRW; 199,000 / 250,000 = ~0.8 days
        assert res.payback_days <= 1.0

    def test_extreme_large_revenue_scaling(self):
        res = ScenarioEngine.calculate_scenarios("MANUFACTURING", 10_000_000_000, 199000)
        assert res.scenarios["baseline"].monthly_gain_krw == 2_000_000_000
        assert res.payback_days < 0.1

    def test_unknown_category_fallback(self):
        res = ScenarioEngine.calculate_scenarios("UNKNOWN_DOMAIN", 20000000, 49000)
        # Defaults to 0.17 (same as FNB)
        assert res.scenarios["baseline"].monthly_gain_krw == int(20000000 * 0.17)

    def test_all_five_categories_comparative_matrix(self):
        rev = 30000000
        r_fnb = ScenarioEngine.calculate_scenarios("FNB", rev).scenarios["baseline"].monthly_gain_krw
        r_beauty = ScenarioEngine.calculate_scenarios("BEAUTY", rev).scenarios["baseline"].monthly_gain_krw
        r_med = ScenarioEngine.calculate_scenarios("MEDICAL", rev).scenarios["baseline"].monthly_gain_krw
        r_saas = ScenarioEngine.calculate_scenarios("SAAS", rev).scenarios["baseline"].monthly_gain_krw
        r_mfg = ScenarioEngine.calculate_scenarios("MANUFACTURING", rev).scenarios["baseline"].monthly_gain_krw

        # SAAS (22%) > MFG (20%) > BEAUTY (19%) > FNB (17%) > MEDICAL (15%)
        assert r_saas > r_mfg > r_beauty > r_fnb > r_med


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

    def test_multiple_rejection_history_accumulation(self):
        FeedbackLearner.record_feedback("TENANT_001", "DISCOUNT_TOO_HIGH", "마진 부족 1")
        FeedbackLearner.record_feedback("TENANT_001", "TIMING_MISMATCH", "시간대 부적합")
        FeedbackLearner.record_feedback("TENANT_001", "DISCOUNT_TOO_HIGH", "마진 부족 2")

        constraints = FeedbackLearner.get_tenant_constraints("TENANT_001")
        assert len(constraints) == 3
        # Most recent first
        assert constraints[0].reason_code == "DISCOUNT_TOO_HIGH"
        assert constraints[1].reason_code == "TIMING_MISMATCH"

    def test_feedback_statistics_counts(self):
        FeedbackLearner.record_feedback("TENANT_003", "DISCOUNT_TOO_HIGH")
        FeedbackLearner.record_feedback("TENANT_003", "DISCOUNT_TOO_HIGH")
        FeedbackLearner.record_feedback("TENANT_003", "TONE_TOO_CASUAL")

        stats = FeedbackLearner.get_feedback_statistics("TENANT_003")
        assert stats["tenant_id"] == "TENANT_003"
        assert stats["total_rejections"] == 3
        assert stats["counts_by_reason"]["DISCOUNT_TOO_HIGH"] == 2
        assert stats["counts_by_reason"]["TONE_TOO_CASUAL"] == 1

    def test_clear_tenant_constraints(self):
        FeedbackLearner.record_feedback("TENANT_004", "WRONG_AUDIENCE")
        assert len(FeedbackLearner.get_tenant_constraints("TENANT_004")) == 1

        FeedbackLearner.clear_tenant_constraints("TENANT_004")
        assert len(FeedbackLearner.get_tenant_constraints("TENANT_004")) == 0

    def test_unknown_reason_code_fallback_rule(self):
        c = FeedbackLearner.record_feedback("TENANT_001", "CUSTOM_UNRECOGNIZED_REASON")
        assert c.reason_code == "CUSTOM_UNRECOGNIZED_REASON"
        assert "기본 가이드라인 준수" in c.applied_rule

    def test_ab_variant_empty_title_and_body_fallback(self):
        variants = FeedbackLearner.generate_ab_variants(
            campaign_id="CAMP-EMPTY-01",
            tenant_id="TENANT_001",
            base_title="",
            base_body="   ",
        )
        assert "특별 타임어택" in variants.variant_a.headline
        assert "특급 프로모션" in variants.variant_a.body

    def test_ab_variant_retrieval_by_campaign_id(self):
        variants = FeedbackLearner.generate_ab_variants(
            campaign_id="CAMP-LOOKUP-01",
            tenant_id="TENANT_001",
            base_title="가을 한정 신메뉴",
            base_body="얼리버드 쿠폰",
        )
        fetched = FeedbackLearner.get_campaign_variants("CAMP-LOOKUP-01")
        assert fetched is not None
        assert fetched.campaign_id == "CAMP-LOOKUP-01"


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

    def test_submit_draft_nonexistent_deal_raises(self):
        with pytest.raises(ValueError, match="Deal NONEXISTENT not found"):
            creator_network.submit_draft("NONEXISTENT", "https://cdn.aim.link/v.mp4")

    def test_submit_draft_on_settled_deal_raises(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        creator_network.approve_draft_and_release_base(deal.deal_id)
        creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="VIEWS", metric_value=60000)
        assert deal.status == "SETTLED"

        with pytest.raises(ValueError, match="이미 정산 완료된 계약"):
            creator_network.submit_draft(deal.deal_id, "https://cdn.aim.link/new.mp4")

    def test_approve_draft_already_released_raises(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        creator_network.approve_draft_and_release_base(deal.deal_id)

        with pytest.raises(ValueError, match="이미 기본 정산금이 지급된 계약"):
            creator_network.approve_draft_and_release_base(deal.deal_id)

    def test_unlock_milestone_already_settled_raises(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        creator_network.approve_draft_and_release_base(deal.deal_id)
        creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="VIEWS", metric_value=55000)

        with pytest.raises(ValueError, match="이미 최종 정산이 완료된 계약"):
            creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="VIEWS", metric_value=70000)

    def test_unlock_milestone_before_base_payout_raises(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        # status is ESCROW_LOCKED
        with pytest.raises(ValueError, match="1차 기본 정산금 지급이 완료된 후에만"):
            creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="VIEWS", metric_value=80000)

    def test_unlock_milestone_via_conversions(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        creator_network.approve_draft_and_release_base(deal.deal_id)

        # Conversions < 20 fails
        with pytest.raises(ValueError, match="성과 마일스톤 기준 미달"):
            creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="CONVERSIONS", metric_value=18)

        # Conversions >= 20 succeeds
        res = creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="CONVERSIONS", metric_value=25)
        assert res["status"] == "SETTLED"
        assert res["metric_type"] == "CONVERSIONS"
        assert res["metric_value"] == 25

    def test_unlock_milestone_invalid_metric_type_fails(self):
        deal = creator_network.create_escrow_deal("TENANT_001", "CR_FNB_02", "BRIEF_01")
        creator_network.approve_draft_and_release_base(deal.deal_id)

        with pytest.raises(ValueError, match="성과 마일스톤 기준 미달"):
            creator_network.unlock_milestone_bonus(deal.deal_id, metric_type="LIKES", metric_value=100000)

    def test_request_revision_nonexistent_deal_raises(self):
        with pytest.raises(ValueError, match="Deal NONEXISTENT not found"):
            creator_network.request_revision("NONEXISTENT", "수정 요청")


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

    def test_single_channel_touchpoint_full_attribution(self):
        res = CrossAttributionEngine.deduplicate_transaction(
            tenant_id="TENANT_001",
            customer_id="CUST_SINGLE",
            order_amount_krw=50000,
            channels=["POS_COUPON"],
        )
        assert len(res.touchpoints) == 1
        assert res.touchpoints[0].shapley_weight == 1.0
        assert res.touchpoints[0].attributed_amount_krw == 50000
        assert res.deduplication_saved_krw == 0

    def test_empty_channels_fallback_to_direct(self):
        res = CrossAttributionEngine.deduplicate_transaction(
            tenant_id="TENANT_001",
            customer_id="CUST_NONE",
            order_amount_krw=30000,
            channels=[],
        )
        assert len(res.touchpoints) == 1
        assert res.touchpoints[0].channel == "DIRECT"
        assert res.touchpoints[0].attributed_amount_krw == 30000

    def test_zero_order_amount_transaction(self):
        res = CrossAttributionEngine.deduplicate_transaction(
            tenant_id="TENANT_001",
            customer_id="CUST_ZERO",
            order_amount_krw=0,
            channels=["UTM_SHORTS", "POS_COUPON"],
        )
        assert res.actual_order_amount_krw == 0
        assert res.raw_claimed_total_krw == 0
        assert res.revenue_split["platform_fee_krw"] == 0
        assert res.revenue_split["creator_bonus_krw"] == 0
        assert res.revenue_split["merchant_net_revenue_krw"] == 0

    def test_negative_order_amount_normalized(self):
        res = CrossAttributionEngine.deduplicate_transaction(
            tenant_id="TENANT_001",
            customer_id="CUST_NEG",
            order_amount_krw=-20000,
            channels=["POS_COUPON"],
        )
        assert res.actual_order_amount_krw == 0

    def test_all_five_channels_simultaneous_attribution(self):
        all_channels = ["UTM_SHORTS", "KAKAO_ALERT", "POS_COUPON", "RECEIPT_OCR", "VIRTUAL_NUMBER"]
        res = CrossAttributionEngine.deduplicate_transaction(
            tenant_id="TENANT_001",
            customer_id="CUST_ALL5",
            order_amount_krw=100000,
            channels=all_channels,
        )
        assert len(res.touchpoints) == 5
        assert res.raw_claimed_total_krw == 500000
        assert res.deduplication_saved_krw == 400000

        total_weight = sum(t.shapley_weight for t in res.touchpoints)
        assert total_weight == pytest.approx(1.0, abs=0.01)

        total_attr = sum(t.attributed_amount_krw for t in res.touchpoints)
        assert total_attr == 100000

    def test_monthly_statement_zero_fee_no_division_error(self):
        stmt = CrossAttributionEngine.generate_monthly_statement(
            tenant_id="TENANT_FREE",
            business_name="무료 체험 사업장",
            cumulative_gmv=1000000,
            monthly_fee=0,
        )
        assert stmt.saas_subscription_fee_krw == 0
        assert stmt.roi_multiple == 0.0
        assert stmt.net_payout_to_merchant_krw == stmt.merchant_net_revenue_krw

    def test_monthly_statement_negative_net_payout(self):
        stmt = CrossAttributionEngine.generate_monthly_statement(
            tenant_id="TENANT_LOW",
            business_name="초기 저조 사업장",
            cumulative_gmv=10000,  # 89% = 8,900 KRW
            monthly_fee=49000,
        )
        # 8,900 - 49,000 = -40,100 KRW
        assert stmt.net_payout_to_merchant_krw < 0


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

    def test_circuit_breaker_resolution_workflow(self):
        rec = MasterAdminConsole.scan_and_trip_circuit_breaker(
            tenant_id="TENANT_002",
            anomaly_type="RAPID_COUPON_BURST",
            evidence_payload={"rate": "30/min"},
        )
        circuit_id = rec["circuit_id"]

        # Health is active before resolution
        status_before = MasterAdminConsole.get_circuit_breaker_status()
        assert status_before["health"] == "CIRCUIT_TRIPPED_ACTIVE"
        assert status_before["currently_frozen_count"] == 1

        # Resolve incident
        resolved = MasterAdminConsole.resolve_circuit_breaker(
            circuit_id=circuit_id,
            reviewer="보안 총괄 이사",
            resolution_notes="IP 차단 조치 후 격리 해제",
        )
        assert resolved["status"] == "RESOLVED_SAFE"
        assert resolved["resolved_by"] == "보안 총괄 이사"
        assert "resolved_at" in resolved

        # Health returns to PROTECTED
        status_after = MasterAdminConsole.get_circuit_breaker_status()
        assert status_after["health"] == "PROTECTED"
        assert status_after["currently_frozen_count"] == 0

    def test_resolve_nonexistent_circuit_id_raises(self):
        with pytest.raises(ValueError, match="Circuit breaker incident NONEXISTENT not found"):
            MasterAdminConsole.resolve_circuit_breaker("NONEXISTENT")

    def test_peer_benchmark_all_five_domains(self):
        # TENANT_001 = fnb, 002 = medical, 003 = beauty, 004 = b2b_saas, 005 = manufacturing
        tids = ["TENANT_001", "TENANT_002", "TENANT_003", "TENANT_004", "TENANT_005"]
        expected_domains = ["fnb", "medical", "beauty", "b2b_saas", "manufacturing"]
        for tid, expected_dom in zip(tids, expected_domains):
            bench = MasterAdminConsole.get_peer_benchmark(tid)
            assert bench["tenant_id"] == tid
            assert bench["domain"] == expected_dom
            assert bench["peers_analyzed_count"] > 0
            assert bench["peer_average_revenue_krw"] > 0

    def test_peer_benchmark_domain_aliases(self):
        # Create temporary custom tenant with alias "saas"
        t_saas = TenantManager.get_tenant("TENANT_004")
        orig_dom = t_saas.domain
        try:
            t_saas.domain = "saas"
            bench = MasterAdminConsole.get_peer_benchmark("TENANT_004")
            # Should correctly map to b2b_saas threshold (19 peers)
            assert bench["peers_analyzed_count"] == 19
        finally:
            t_saas.domain = orig_dom

    def test_peer_benchmark_ranking_levels(self):
        # 1. Top tier (> 10M for b2b_saas -> TENANT_004 has 16.8M)
        b_top = MasterAdminConsole.get_peer_benchmark("TENANT_004")
        assert "상위 5% 최우수" in b_top["rank_label"]
        assert b_top["percentile_score"] >= 90.0


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

    def test_api_creator_draft_submit_nonexistent_deal_404(self, client):
        r = client.post(
            "/api/v1/creator/deal/NONEXISTENT/draft/submit",
            json={"video_url": "https://cdn.aim.link/v.mp4", "compliance_passed": True},
        )
        assert r.status_code == 404
        assert "not found" in r.json()["error"].lower()

    def test_api_creator_draft_approve_nonexistent_deal_404(self, client):
        r = client.post("/api/v1/creator/deal/NONEXISTENT/draft/approve")
        assert r.status_code == 404

    def test_api_creator_draft_revision_nonexistent_deal_404(self, client):
        r = client.post(
            "/api/v1/creator/deal/NONEXISTENT/draft/revision",
            json={"feedback": "수정 요망"},
        )
        assert r.status_code == 404

    def test_api_creator_milestone_unlock_nonexistent_deal_404(self, client):
        r = client.post(
            "/api/v1/creator/deal/NONEXISTENT/milestone/unlock",
            json={"metric_type": "VIEWS", "metric_value": 60000},
        )
        assert r.status_code == 404

    def test_api_creator_milestone_unlock_target_unmet_400(self, client):
        # DEAL_7749A is seeded in DRAFT_SUBMITTED
        client.post("/api/v1/creator/deal/DEAL_7749A/draft/approve")
        r = client.post(
            "/api/v1/creator/deal/DEAL_7749A/milestone/unlock",
            json={"metric_type": "VIEWS", "metric_value": 15000},
        )
        assert r.status_code == 400
        assert "기준 미달" in r.json()["error"]

    def test_api_circuit_breaker_resolve_success_and_404(self, client):
        # 1. Trip anomaly
        r_sim = client.post(
            "/api/v1/admin/circuit-breaker/simulate-anomaly",
            json={
                "tenant_id": "TENANT_001",
                "anomaly_type": "DUPLICATE_RECEIPT_FRAUD",
                "evidence": {"receipt": "REC-77"},
            },
        )
        cid = r_sim.json()["circuit_breaker"]["circuit_id"]

        # 2. Resolve successfully
        r_res = client.post(
            f"/api/v1/admin/circuit-breaker/{cid}/resolve",
            json={"reviewer": "보안팀장", "resolution_notes": "이상 없음 확인"},
        )
        assert r_res.status_code == 200
        assert r_res.json()["circuit_breaker"]["status"] == "RESOLVED_SAFE"

        # 3. 404 on invalid circuit ID
        r_invalid = client.post(
            "/api/v1/admin/circuit-breaker/CB_NONEXISTENT/resolve",
            json={"reviewer": "보안팀장"},
        )
        assert r_invalid.status_code == 404

    def test_api_peer_benchmark_nonexistent_tenant_404(self, client):
        r = client.get("/api/v1/admin/fleet/benchmark/TENANT_NONEXISTENT")
        assert r.status_code == 404

    def test_api_scenario_calculate_zero_payload(self, client):
        r = client.post(
            "/api/v1/scenario/calculate",
            json={"category": "FNB", "revenue": 0, "monthly_fee": 0},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["monthly_revenue_krw"] == 0
        assert data["payback_days"] == 0.0

    def test_api_reject_with_feedback_nonexistent_campaign_404(self, client):
        r = client.post(
            "/api/v1/tenant/campaign/CAMP-NONEXISTENT/reject-with-feedback",
            json={"reason_code": "TONE_TOO_CASUAL"},
        )
        assert r.status_code == 404

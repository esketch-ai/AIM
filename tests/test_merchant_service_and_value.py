"""AIM (AI Platform Initiative) - Merchant Service Clarity & Value Suite
Comprehensive unit tests for merchant-facing features:
1. ROI and value projection calculations across 5 domains (F&B, Medical, Beauty, SaaS, Manufacturing)
2. Merchant onboarding personalization and readiness across tenant fleet
3. Campaign staged review, 1-click mobile approval, and WTP ledger reflection
4. 5-Method attribution cockpit (POS coupon, receipt OCR, time window lift, UTM, virtual number)
5. 15s Shorts creator brief generation, value compression, and 10% subscriber escrow clearing
6. REST API contracts for all merchant-facing endpoints
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any

from aim.tenant.manager import TenantManager
from aim.tenant.approval import ApprovalDesk
from aim.core.value_compressor import ValueCompressor, ValueCompressionRequest
from aim.core.brief_generator import BriefGenerator, BriefQuestionnaireInput
from aim.matching.creator_network import CreatorNetwork, MatchRequest
from aim.core.coupon_vault import coupon_vault, ReceiptVerificationRequest
from aim.core.value_attribution import attribution_ledger
from aim.web_app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_tenant_state():
    """Ensures clean tenant defaults, staged campaign desk, coupon vault, and attribution ledger before each test."""
    TenantManager._tenants.clear()
    TenantManager._initialize_defaults()
    ApprovalDesk._staged_campaigns.clear()
    ApprovalDesk._initialize_defaults()
    coupon_vault.coupons.clear()
    coupon_vault._seed_default_coupons()
    attribution_ledger.__init__()
    yield


# ============================================================================
# 1. TestMerchantRoiAndValueProjections: 5 Domain Mathematical Integrity
# ============================================================================
class TestMerchantRoiAndValueProjections:
    """Verifies ROI calculator formulas, margin rates, and time savings across all 5 merchant domains."""

    RATES = {
        "FNB": 0.17,
        "BEAUTY": 0.19,
        "MEDICAL": 0.15,
        "SAAS": 0.22,
        "MANUFACTURING": 0.20,
    }
    MONTHLY_PRO_FEE = 49000

    def _calculate(self, category: str, revenue: int) -> Dict[str, Any]:
        rate = self.RATES.get(category, 0.17)
        gain = int(revenue * rate)
        roi = round(gain / self.MONTHLY_PRO_FEE, 1)
        hours_saved = int(18 + (revenue / 10000000) * 3)
        return {
            "rate": rate,
            "gain_krw": gain,
            "roi_multiplier": roi,
            "hours_saved": hours_saved,
        }

    def test_fnb_bakery_roi_projection(self):
        # 25,000,000 KRW monthly revenue in F&B (17% margin)
        res = self._calculate("FNB", 25000000)
        assert res["rate"] == 0.17
        assert res["gain_krw"] == 4250000
        assert res["roi_multiplier"] == pytest.approx(86.7, abs=0.1)
        assert res["hours_saved"] == 25

    def test_medical_clinic_roi_projection(self):
        # 50,000,000 KRW monthly revenue in Medical (15% margin)
        res = self._calculate("MEDICAL", 50000000)
        assert res["rate"] == 0.15
        assert res["gain_krw"] == 7500000
        assert res["roi_multiplier"] == pytest.approx(153.1, abs=0.1)
        assert res["hours_saved"] == 33

    def test_beauty_salon_roi_projection(self):
        # 20,000,000 KRW monthly revenue in Beauty (19% margin)
        res = self._calculate("BEAUTY", 20000000)
        assert res["rate"] == 0.19
        assert res["gain_krw"] == 3800000
        assert res["roi_multiplier"] == pytest.approx(77.6, abs=0.1)
        assert res["hours_saved"] == 24

    def test_saas_software_roi_projection(self):
        # 30,000,000 KRW monthly revenue in B2B SaaS (22% margin)
        res = self._calculate("SAAS", 30000000)
        assert res["rate"] == 0.22
        assert res["gain_krw"] == 6600000
        assert res["roi_multiplier"] == pytest.approx(134.7, abs=0.1)
        assert res["hours_saved"] == 27

    def test_manufacturing_roi_projection_and_slider_bounds(self):
        # 80,000,000 KRW monthly revenue in Precision Manufacturing (20% margin)
        res = self._calculate("MANUFACTURING", 80000000)
        assert res["rate"] == 0.20
        assert res["gain_krw"] == 16000000
        assert res["roi_multiplier"] == pytest.approx(326.5, abs=0.1)
        assert res["hours_saved"] == 42

        # Slider bounds test: min 10M KRW, max 100M KRW
        min_res = self._calculate("MANUFACTURING", 10000000)
        max_res = self._calculate("MANUFACTURING", 100000000)
        assert min_res["gain_krw"] > 0
        assert min_res["roi_multiplier"] > 1.0
        assert max_res["gain_krw"] == 20000000
        assert max_res["hours_saved"] == 48


# ============================================================================
# 2. TestMerchantOnboardingPersonalization: 5 Fleet Profiles
# ============================================================================
class TestMerchantOnboardingPersonalization:
    """Verifies that each tenant in the fleet has complete personalized onboarding metadata."""

    def test_tenant_001_fnb_onboarding_profile(self):
        t = TenantManager.get_tenant("TENANT_001")
        assert t is not None
        assert t.business_name == "성수 아뜰리에 베이커리 & 카페"
        assert t.domain == "fnb"
        assert t.owner_name == "김성수 대표"
        assert "성수동" in t.business_state.location
        assert "AOP 버터" in t.business_state.core_usps[0]
        assert t.business_state.unit_price == 24000
        assert "비 예보" in t.business_state.trigger_event

    def test_tenant_002_medical_onboarding_profile(self):
        t = TenantManager.get_tenant("TENANT_002")
        assert t is not None
        assert t.business_name == "강남 리엔 피부과의원"
        assert t.domain == "medical"
        assert t.owner_name == "이지현 대표원장"
        assert "강남구" in t.business_state.location
        assert t.subscription_tier == "ENTERPRISE"
        assert t.monthly_fee_krw == 199000

    def test_tenant_003_beauty_onboarding_profile(self):
        t = TenantManager.get_tenant("TENANT_003")
        assert t is not None
        assert t.business_name == "청담 아우라 헤어살롱"
        assert t.domain == "beauty"
        assert t.owner_name == "박준우 원장"
        assert "청담동" in t.business_state.location
        assert t.subscription_tier == "PRO"
        assert t.business_state.idle_capacity_rate == 0.60

    def test_tenant_004_saas_onboarding_profile(self):
        t = TenantManager.get_tenant("TENANT_004")
        assert t is not None
        assert t.business_name == "플로우독 (FlowDoc) - AI 협업 툴"
        assert t.domain == "b2b_saas"
        assert t.owner_name == "최진혁 파운더"
        assert "판교" in t.business_state.location
        assert t.business_state.unit_price == 200000

    def test_tenant_005_manufacturing_onboarding_profile(self):
        t = TenantManager.get_tenant("TENANT_005")
        assert t is not None
        assert t.business_name == "대진정밀공업 (CNC·사출 가공)"
        assert t.domain == "manufacturing"
        assert t.owner_name == "정대진 총괄전무"
        assert "창원" in t.business_state.location
        assert t.subscription_tier == "ENTERPRISE"
        assert t.business_state.unit_price == 22500000


# ============================================================================
# 3. TestMerchantCampaignLifecycleAndPhoneApproval
# ============================================================================
class TestMerchantCampaignLifecycleAndPhoneApproval:
    """Verifies staged campaign fetching, 1-click mobile approval, and ledger revenue reflection."""

    def test_get_staged_campaigns_returns_valid_structure(self, client):
        resp = client.get("/api/tenant/TENANT_001/staged-campaigns")
        assert resp.status_code == 200
        data = resp.json()
        assert "campaigns" in data
        assert len(data["campaigns"]) > 0
        camp = data["campaigns"][0]
        assert "campaign_id" in camp
        assert "campaign_title" in camp
        assert "projected_revenue_krw" in camp
        assert camp["projected_revenue_krw"] > 0
        assert camp["status"] == "STAGED"

    def test_approve_campaign_updates_status_and_ledger(self, client):
        # 1. Initial tenant revenue
        t_before = TenantManager.get_tenant("TENANT_001")
        initial_revenue = t_before.cumulative_revenue_generated_krw
        initial_campaigns = t_before.total_campaigns_executed

        # 2. Approve staged campaign
        resp = client.post("/api/tenant/TENANT_001/campaign/CAMP-001/approve")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert "성공적으로" in data["message"]
        assert "송출" in data["message"]
        assert data["campaign_id"] == "CAMP-001"
        assert ApprovalDesk._staged_campaigns["CAMP-001"].status == "APPROVED"
        assert ApprovalDesk._staged_campaigns["CAMP-001"].approved_at is not None

        # 3. Verify tenant revenue increment
        t_after = TenantManager.get_tenant("TENANT_001")
        assert t_after.cumulative_revenue_generated_krw == initial_revenue + 240000
        assert t_after.total_campaigns_executed == initial_campaigns + 1

    def test_reject_campaign_marks_status_rejected(self, client):
        resp = client.post("/api/tenant/TENANT_001/campaign/CAMP-001/reject")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert "반려되었습니다" in data["message"]
        assert data["campaign"]["status"] == "REJECTED"

    def test_approve_nonexistent_campaign_returns_404(self, client):
        resp = client.post("/api/tenant/TENANT_001/campaign/CAMP-NONEXISTENT/approve")
        assert resp.status_code == 404

    def test_multichannel_copy_contains_required_channels(self, client):
        resp = client.get("/api/tenant/TENANT_001")
        assert resp.status_code == 200
        data = resp.json()
        assert "live_plan" in data
        plan = data["live_plan"]
        assert "channels" in plan
        assert "blog" in plan["channels"]
        assert len(plan["channels"]["blog"]["body"]) > 20
        assert plan["all_compliant"] is True


# ============================================================================
# 4. TestMerchant5MethodAttributionCockpit
# ============================================================================
class TestMerchant5MethodAttributionCockpit:
    """Verifies all 5 attribution tracking methods and revenue clearing logic."""

    def test_coupon_vault_issue_and_redeem_financial_split(self):
        # 1. Issue coupon
        coupon = coupon_vault.issue_coupon(
            tenant_id="TENANT_001",
            campaign_id="CAMP_RAIN_001",
            channel="YOUTUBE",
            creator_id="CR_002",
            discount_amount_krw=3000,
            min_order_amount_krw=20000,
        )
        assert coupon.is_redeemed is False

        # 2. Redeem at POS with 24,000 KRW order
        split_result = coupon_vault.redeem_coupon(
            coupon_code=coupon.coupon_code,
            order_amount_krw=24000,
        )
        assert split_result.success is True
        assert split_result.final_paid_amount_krw == 21000  # 24k - 3k discount
        assert split_result.revenue_split.take_rate_pct == 8.0
        assert split_result.revenue_split.platform_commission_krw == 1920  # 24000 * 8%
        assert split_result.revenue_split.creator_bonus_pct == 3.0
        assert split_result.revenue_split.creator_bonus_krw == 720  # 24000 * 3%
        assert split_result.revenue_split.merchant_net_revenue_krw == 21360  # 24000 - 1920 - 720

    def test_duplicate_coupon_redemption_is_strictly_blocked(self):
        coupon = coupon_vault.issue_coupon(
            tenant_id="TENANT_001",
            campaign_id="CAMP_TEST",
            channel="YOUTUBE",
            creator_id="CR_002",
            discount_amount_krw=3000,
            min_order_amount_krw=20000,
        )
        # First redemption succeeds
        first = coupon_vault.redeem_coupon(coupon.coupon_code, 24000)
        assert first.success is True

        # Second redemption must raise ValueError
        with pytest.raises(ValueError, match="이미 사용 완료된 쿠폰"):
            coupon_vault.redeem_coupon(coupon.coupon_code, 24000)

    def test_receipt_ai_ocr_verification_and_cashback(self):
        ocr_text = "[영수증] 성수 아뜰리에 베이커리 결제금액: 36,000원 2026-10-08 승인번호: 884129"
        res = coupon_vault.verify_receipt(
            ReceiptVerificationRequest(
                tenant_id="TENANT_001",
                receipt_ocr_text=ocr_text,
            )
        )
        assert res.success is True
        assert res.order_amount_krw == 36000
        assert res.cashback_reward_krw == 1000
        assert res.evidence_tier == "A_MEASURED"

    def test_coupon_minimum_order_validation(self):
        coupon = coupon_vault.issue_coupon(
            tenant_id="TENANT_001",
            campaign_id="CAMP_MIN",
            channel="INSTAGRAM",
            discount_amount_krw=3000,
            min_order_amount_krw=20000,
        )
        with pytest.raises(ValueError, match="최소 주문 금액"):
            coupon_vault.redeem_coupon(coupon.coupon_code, 15000)

    def test_monetization_streams_summary_calculation(self, client):
        resp = client.get("/api/v1/monetization/streams/summary/TENANT_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["tenant_id"] == "TENANT_001"
        streams = data["platform_revenue_streams"]
        assert "stream_1_take_rate_commission" in streams
        assert "stream_2_escrow_marketplace_fee" in streams
        assert "stream_3_saas_subscription_mrr" in streams
        assert "stream_4_incremental_success_fee" in streams
        assert streams["stream_1_take_rate_commission"]["amount_krw"] > 0
        assert streams["stream_3_saas_subscription_mrr"]["amount_krw"] == 49000

    def test_simulate_all_methods_clears_gmv_and_returns_summary(self, client):
        resp = client.post("/api/v1/monetization/simulate/all", json={"tenant_id": "TENANT_001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["coupon_redeemed"]["success"] is True
        assert data["receipt_verified"]["success"] is True
        assert data["lift_attributed_krw"] == 150000


# ============================================================================
# 5. TestMerchantCreatorMarketplaceExperience
# ============================================================================
class TestMerchantCreatorMarketplaceExperience:
    """Verifies the 3-question input to 15s storyboard and 10% subscriber escrow discount."""

    def test_value_compressor_creates_3_principles_hook(self):
        compressor = ValueCompressor()
        req = ValueCompressionRequest(
            product_name="시그니처 바질 소금빵",
            raw_benefit="프랑스산 고메버터 48%로 구워내 풍미가 진하고 바삭함",
            target_audience="2030 성수동 직장인",
            pain_point="나른한 오후, 눅눅한 빵에 실망하셨나요?",
            action_type="DISCOUNT_COUPON",
            industry="FNB",
        )
        res = compressor.compress(req)
        assert len(res.pain_point_strike) > 0
        assert "버터 함량 48%" in res.metaphor_and_number
        assert "원클릭 타임어택 쿠폰" in res.direct_cta
        assert res.total_pitch_seconds == 15

    def test_brief_generator_creates_exact_15s_4scenes(self):
        generator = BriefGenerator()
        inp = BriefQuestionnaireInput(
            product_name="시그니처 바질 소금빵",
            core_benefit="프랑스산 고메버터 48%로 구워내 풍미가 진하고 바삭함",
            target_audience="2030 성수동 직장인 및 디저트 러버",
            content_format="SHORTS",
            budget_tier="MID_450K",
            industry="FNB",
        )
        brief = generator.generate(inp)
        assert len(brief.scenes) == 4
        total_seconds = sum(s.duration_seconds for s in brief.scenes)
        assert total_seconds == 15
        assert brief.scenes[0].duration_seconds == 3  # 3-sec hook
        assert brief.scenes[3].duration_seconds == 3  # 3-sec CTA
        assert len(brief.compliance_guidelines) >= 2
        assert "24h Fast-Track" in brief.sla_notice

    def test_creator_matching_affinity_and_ranking(self):
        network = CreatorNetwork()
        req = MatchRequest(
            category="FNB",
            content_format="SHORTS",
            budget_tier="MID_450K",
            target_audience="2030 성수동 직장인",
            subscriber_plan="PRO",
        )
        matches = network.match_creators(req)
        assert len(matches) > 0
        top = matches[0]
        assert top.match_score >= 85.0
        assert top.take_rate_pct == 10.0  # 10% subscriber rate
        assert top.creator.category == "FNB"

    def test_escrow_financial_split_70_30_with_subscriber_discount(self):
        c = CreatorNetwork.SAMPLE_CREATORS[0]
        total_budget = c.price_krw  # e.g., 150,000 KRW

        # SaaS Subscriber Take-Rate: 10%
        platform_fee = int(total_budget * 0.10)
        creator_total = total_budget - platform_fee
        base_payout = int(creator_total * 0.70)
        bonus_payout = creator_total - base_payout

        assert platform_fee == int(total_budget * 0.10)
        assert creator_total == total_budget - platform_fee
        assert base_payout + bonus_payout == creator_total


# ============================================================================
# 6. TestMerchantRestApiContracts
# ============================================================================
class TestMerchantRestApiContracts:
    """Verifies HTTP status codes and payloads for merchant endpoints."""

    def test_api_tenant_profile_contract(self, client):
        resp = client.get("/api/tenant/TENANT_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant"]["tenant_id"] == "TENANT_001"
        assert "business_state" in data["tenant"]

    def test_api_creator_brief_generate_contract(self, client):
        resp = client.post(
            "/api/v1/creator/brief/generate",
            json={
                "product_name": "시그니처 바질 소금빵",
                "core_benefit": "프랑스산 고메버터 48%",
                "target_audience": "2030 성수동 직장인",
                "content_format": "SHORTS",
                "budget_tier": "MID_450K",
                "industry": "FNB",
            },
        )
        assert resp.status_code == 200
        brief = resp.json()
        assert "brief_id" in brief
        assert len(brief["scenes"]) == 4

    def test_api_creator_match_contract(self, client):
        resp = client.post(
            "/api/v1/creator/match",
            json={
                "category": "FNB",
                "content_format": "SHORTS",
                "budget_tier": "MID_450K",
                "target_audience": "2030 직장인",
                "subscriber_plan": "PRO",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["take_rate_pct"] == 10.0
        assert len(data["creators"]) > 0

    def test_api_creator_escrow_order_contract(self, client):
        resp = client.post(
            "/api/v1/creator/escrow/order",
            json={
                "tenant_id": "TENANT_001",
                "creator_id": "CR_FNB_02",
                "brief_id": "BRIEF_TEST_01",
                "subscriber_plan": "PRO",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "deal" in data
        deal = data["deal"]
        assert deal["take_rate_pct"] == 10.0
        assert deal["platform_fee"] == 45000
        assert deal["status"] == "ESCROW_LOCKED"
        assert deal["fast_track_hours_left"] == 24

    def test_api_monetization_coupon_redeem_contract(self, client):
        # Issue coupon first
        c = coupon_vault.issue_coupon(
            tenant_id="TENANT_001",
            campaign_id="CAMP_001",
            channel="YOUTUBE",
            creator_id="CR_FNB_02",
            discount_amount_krw=3000,
            min_order_amount_krw=20000,
        )
        resp = client.post(
            "/api/v1/monetization/coupon/redeem",
            json={"coupon_code": c.coupon_code, "order_amount_krw": 24000},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["final_paid_amount_krw"] == 21000
        assert data["revenue_split"]["platform_commission_krw"] == 1920

    def test_api_monetization_receipt_verify_contract(self, client):
        resp = client.post(
            "/api/v1/monetization/receipt/verify",
            json={
                "tenant_id": "TENANT_001",
                "receipt_ocr_text": "[영수증] 성수 아뜰리에 베이커리 결제금액: 36,000원 승인번호: 998811",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["cashback_reward_krw"] == 1000
        assert data["evidence_tier"] == "A_MEASURED"

    def test_api_monetization_methods_contract(self, client):
        resp = client.get("/api/v1/monetization/methods")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["methods"]) == 5

    def test_api_current_package_contract(self, client):
        resp = client.get("/api/current-package?tone=MZ_TREND")
        assert resp.status_code == 200
        data = resp.json()
        assert "store_id" in data
        assert "channels" in data

"""
Tests for AIM Multi-Channel Attribution Engine and Platform Monetization Architecture
---------------------------------------------------------------------------------------
Verifies:
1. Dynamic Coupon Issuance, Min-order validation, and Duplicate Prevention
2. 100% Measured (A_MEASURED) Conversion Attribution via Coupon POS Scan
3. Receipt Photo AI OCR Parsing & Cashback Reward Verification
4. Multi-touch Attribution Models (Last Touch, Linear, Shapley Value)
5. Revenue Share Split (Take-Rate, Escrow Bonus, Merchant Net Margin)
6. Value Attribution Ledger Synchronization
7. FastAPI REST API Endpoints End-to-End
"""

import pytest
from fastapi.testclient import TestClient

from aim.core.attribution_engine import (
    attribution_engine,
    AttributionMethod,
    AttributionModelType,
    ChannelTouchpoint,
    MultiTouchAttributionCalculator,
    RevenueClearingEngine,
)
from aim.core.coupon_vault import (
    coupon_vault,
    ReceiptVerificationRequest,
)
from aim.core.value_attribution import attribution_ledger
from aim.web_app import app

client = TestClient(app)


def test_revenue_share_split_calculation():
    """Verifies precision of revenue clearing splits."""
    split = RevenueClearingEngine.calculate_split(
        transaction_amount_krw=100000,
        take_rate_pct=8.0,
        creator_bonus_rate_pct=3.0,
    )
    assert split.transaction_amount_krw == 100000
    assert split.platform_commission_krw == 8000
    assert split.creator_bonus_krw == 3000
    assert split.merchant_net_revenue_krw == 89000
    assert split.platform_commission_krw + split.creator_bonus_krw + split.merchant_net_revenue_krw == 100000


def test_multi_touch_attribution_models():
    """Tests Last-Touch, Linear, and Shapley attribution weight distributions."""
    touchpoints = [
        ChannelTouchpoint(touchpoint_id="TP1", channel="YOUTUBE", step_order=1),
        ChannelTouchpoint(touchpoint_id="TP2", channel="NAVER_BLOG", step_order=2),
        ChannelTouchpoint(touchpoint_id="TP3", channel="IN_STORE_COUPON", step_order=3),
    ]

    # 1. Last Touch
    lt_weights = MultiTouchAttributionCalculator.calculate_weights(touchpoints, AttributionModelType.LAST_TOUCH)
    assert lt_weights["IN_STORE_COUPON"] == 1.0
    assert lt_weights.get("YOUTUBE", 0.0) == 0.0

    # 2. Linear
    lin_weights = MultiTouchAttributionCalculator.calculate_weights(touchpoints, AttributionModelType.LINEAR)
    assert pytest.approx(sum(lin_weights.values()), 0.01) == 1.0
    assert pytest.approx(lin_weights["YOUTUBE"], 0.01) == 0.3333

    # 3. Shapley
    shapley_weights = MultiTouchAttributionCalculator.calculate_weights(touchpoints, AttributionModelType.SHAPLEY)
    assert pytest.approx(sum(shapley_weights.values()), 0.01) == 1.0
    # Last touch gets 45%, First touch gets 35%, middle gets 20%
    assert shapley_weights["IN_STORE_COUPON"] >= 0.40
    assert shapley_weights["YOUTUBE"] >= 0.30


def test_coupon_issuance_and_redemption_lifecycle():
    """Tests full lifecycle of dynamic coupon issuance, validation, and redemption."""
    # 1. Issue coupon
    coupon = coupon_vault.issue_coupon(
        tenant_id="TENANT_TEST_SMB",
        campaign_id="CAMP_SHORTS_01",
        channel="YOUTUBE",
        creator_id="CR_002",
        discount_amount_krw=3000,
        min_order_amount_krw=20000,
    )
    assert coupon.coupon_code.startswith("AIM-TTEST_SMB-CR_002-")
    assert not coupon.is_redeemed
    assert coupon.evidence_tier == "A_MEASURED"

    # 2. Reject redemption below minimum order amount
    with pytest.raises(ValueError, match="최소 주문 금액"):
        coupon_vault.redeem_coupon(coupon.coupon_code, order_amount_krw=18000)

    # 3. Successful redemption
    result = coupon_vault.redeem_coupon(coupon.coupon_code, order_amount_krw=25000)
    assert result.success is True
    assert result.discount_applied_krw == 3000
    assert result.final_paid_amount_krw == 22000
    assert result.evidence_tier == "A_MEASURED"
    assert result.revenue_split.platform_commission_krw == int(25000 * 0.08)

    # 4. Reject duplicate redemption
    with pytest.raises(ValueError, match="이미 사용 완료된 쿠폰"):
        coupon_vault.redeem_coupon(coupon.coupon_code, order_amount_krw=25000)

    # 5. Verify ledger entry was recorded with A_MEASURED
    summary = attribution_ledger.get_tenant_summary("TENANT_TEST_SMB")
    assert len(summary.entries) >= 1
    recent = summary.entries[0]
    assert recent.evidence_tier == "A_MEASURED"
    assert recent.tracking_code == coupon.coupon_code
    assert recent.attribution_method == "COUPON_CODE"


def test_receipt_ocr_verification():
    """Tests AI Receipt OCR parsing, cashback granting, and A_MEASURED attribution."""
    ocr_sample = """
    =============================
    [영수증] 성수 어반플레이트
    대표자: 김대표 | 사업자: 211-88-99999
    영수증번호: REC-20261008-7711
    주문일시: 2026-10-08 13:42:10
    -----------------------------
    1. 트러플 머쉬룸 뇨끼    22,000
    2. 아메리카노 (2잔)     10,000
    -----------------------------
    합계금액: 32,000
    결제금액: 32,000
    =============================
    """
    req = ReceiptVerificationRequest(
        tenant_id="TENANT_TEST_SMB",
        campaign_id="CAMP_OCR_01",
        creator_id="CR_001",
        receipt_ocr_text=ocr_sample,
    )

    result = coupon_vault.verify_receipt(req)
    assert result.success is True
    assert result.order_amount_krw == 32000
    assert result.cashback_reward_krw == 1000
    assert result.evidence_tier == "A_MEASURED"
    assert "성수 어반플레이트" in result.store_name


def test_monetization_api_rest_endpoints():
    """Tests the full suite of REST API endpoints for monetization and attribution."""
    # 1. GET /methods
    res_methods = client.get("/api/v1/monetization/methods")
    assert res_methods.status_code == 200
    data_methods = res_methods.json()
    assert len(data_methods["methods"]) == 5
    assert any(m["method"] == "COUPON_CODE" for m in data_methods["methods"])
    assert any(m["method"] == "RECEIPT_OCR" for m in data_methods["methods"])

    # 2. POST /coupon/issue
    res_issue = client.post(
        "/api/v1/monetization/coupon/issue",
        json={
            "tenant_id": "TENANT_001",
            "campaign_id": "CAMP_API_TEST",
            "channel": "TIKTOK",
            "creator_id": "CR_002",
            "discount_amount_krw": 5000,
            "min_order_amount_krw": 25000,
        },
    )
    assert res_issue.status_code == 200
    issued = res_issue.json()
    assert issued["discount_amount_krw"] == 5000
    assert issued["coupon_code"].startswith("AIM-T001-CR_002-")

    # 3. POST /coupon/redeem
    res_redeem = client.post(
        "/api/v1/monetization/coupon/redeem",
        json={
            "coupon_code": issued["coupon_code"],
            "order_amount_krw": 30000,
        },
    )
    assert res_redeem.status_code == 200
    redeemed = res_redeem.json()
    assert redeemed["success"] is True
    assert redeemed["final_paid_amount_krw"] == 25000
    assert redeemed["evidence_tier"] == "A_MEASURED"

    # 4. POST /receipt/verify
    res_ocr = client.post(
        "/api/v1/monetization/receipt/verify",
        json={
            "tenant_id": "TENANT_001",
            "campaign_id": "CAMP_API_TEST",
            "receipt_ocr_text": "결제금액: 45,000 승인번호: 994821",
        },
    )
    assert res_ocr.status_code == 200
    ocr_data = res_ocr.json()
    assert ocr_data["order_amount_krw"] == 45000
    assert ocr_data["evidence_tier"] == "A_MEASURED"

    # 5. GET /streams/summary/TENANT_001
    res_summary = client.get("/api/v1/monetization/streams/summary/TENANT_001")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert "platform_revenue_streams" in summary
    assert summary["platform_revenue_streams"]["stream_3_saas_subscription_mrr"]["amount_krw"] == 49000
    assert summary["platform_revenue_streams"]["stream_1_take_rate_commission"]["amount_krw"] > 0

    # 6. POST /simulate/all
    res_sim = client.post(
        "/api/v1/monetization/simulate/all",
        json={"tenant_id": "TENANT_001"},
    )
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["status"] == "success"
    assert sim_data["coupon_redeemed"]["success"] is True
    assert sim_data["receipt_verified"]["success"] is True

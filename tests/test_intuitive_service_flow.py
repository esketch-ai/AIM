"""Tests for Intuitive Service Flow & Expert Assignment Validation
(tests/test_intuitive_service_flow.py)
------------------------------------------------------------------
Validates:
1. Merchant 3-Second Quick Flow & 1-Click Action Approval
2. Instant Value Metric Bar & ROI Summary API
3. Live Value Ledger & POS Scan End-to-End Loop
4. Zero-Install Consumer Mobile Voucher Compliance
"""

import pytest
from fastapi.testclient import TestClient

from aim.web_app import app
from aim.tenant.manager import TenantManager
from aim.core.coupon_vault import coupon_vault
from aim.core.value_attribution import attribution_ledger

client = TestClient(app)


def test_merchant_quick_action_approve():
    """Validates Merchant 3-Second Quick Action 1-click campaign dispatch."""
    res = client.post(
        "/api/v1/tenant/TENANT_001/quick-action/approve",
        json={"custom_trigger": "비 예보 3시간 타임어택 (사장님 1초 퀵 승인)"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["tenant_id"] == "TENANT_001"
    assert "비 예보 3시간 타임어택" in data["campaign_title"]
    assert set(data["dispatched_channels"]) == {"kakao", "instagram", "blog"}
    assert "동시 송출" in data["message"]


def test_instant_value_summary_metrics():
    """Validates the intuitive instant value summary & ROI gauge metrics."""
    res = client.get("/api/v1/tenant/TENANT_001/instant-value-summary")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["tenant_id"] == "TENANT_001"
    assert data["monthly_subscription_krw"] == 49000
    assert data["total_attributed_revenue_krw"] >= 49000
    assert data["net_profit_created_krw"] > 0
    assert data["marketing_roi_pct"] > 0
    assert data["evidence_tier"] == "A_MEASURED"
    assert "입증" in data["human_readable_verdict"]


def test_live_ledger_end_to_end_loop():
    """Validates that POS scan updates live attribution ledger and performs 3-way split."""
    # 1. Issue a coupon
    cp = coupon_vault.issue_coupon(
        tenant_id="TENANT_001",
        campaign_id="CAMP_INTUITIVE_01",
        channel="YOUTUBE",
        creator_id="CR_002",
        discount_amount_krw=3000,
        min_order_amount_krw=15000,
    )

    # 2. Redeem via POS scan
    res_redeem = client.post(
        "/api/v1/monetization/coupon/redeem",
        json={"coupon_code": cp.coupon_code, "order_amount_krw": 25000},
    )
    assert res_redeem.status_code == 200
    data = res_redeem.json()
    assert data["success"] is True
    assert data["discount_applied_krw"] == 3000
    assert data["final_paid_amount_krw"] == 22000
    assert data["revenue_split"]["platform_commission_krw"] == int(25000 * 0.08)
    assert data["revenue_split"]["creator_bonus_krw"] == int(25000 * 0.03)
    assert data["revenue_split"]["merchant_net_revenue_krw"] == 25000 - int(25000 * 0.08) - int(25000 * 0.03)

    # 3. Check attribution ledger records this A_MEASURED event
    summary = attribution_ledger.get_tenant_summary("TENANT_001")
    assert summary.cumulative_revenue_krw > 0
    recent = summary.entries[0]
    assert recent.evidence_tier == "A_MEASURED"


def test_zero_install_mobile_ticket_compliance():
    """Validates zero-app-install mobile voucher compliance for end-consumers."""
    # 1. Issue a coupon
    cp = coupon_vault.issue_coupon(
        tenant_id="TENANT_001",
        campaign_id="CAMP_ZERO_INSTALL",
        channel="INSTAGRAM",
        discount_amount_krw=3000,
        min_order_amount_krw=15000,
    )

    # 2. Access mobile web ticket
    res = client.get(f"/c/{cp.coupon_code}")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert cp.coupon_code in res.text
    assert "3,000" in res.text
    assert "남은 유효 시간" in res.text
    assert "바코드" in res.text

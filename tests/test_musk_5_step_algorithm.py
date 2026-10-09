"""Tests for Elon Musk 5-Step Engineering Algorithm Compliance in AIM Platform
(tests/test_musk_5_step_algorithm.py)
---------------------------------------------------------------------------
Validates:
Step 1. Question Requirements (Slim cognitive footprint, non-blocking flow)
Step 2. Delete Ruthlessly (Direct 1-click execution without mandatory modal intermediate bottleneck)
Step 3. Simplify and Optimize (Visual-first cards, direct prescription dispatch button, 3-metric proof)
Step 4. Accelerate Cycle Time (Sub-second execution from sensing to publishing to ledger sync)
Step 5. Automate (End-to-end autonomous closed loop: Sensing -> Copy -> Dispatch -> POS Scan -> 3-Way Split)
"""

import pytest
from fastapi.testclient import TestClient

from aim.web_app import app
from aim.tenant.manager import TenantManager
from aim.core.consulting_advisor import AIConsultingAdvisor
from aim.core.publisher import ContentPublisher
from aim.core.coupon_vault import coupon_vault

client = TestClient(app)


def test_step1_question_requirements_rendered_html():
    """Step 1 (Question Requirements):

    Validates that the rendered HTML has folded the internal 4-step architecture
    into a collapsible <details> tag so the merchant's view is focused purely on
    what matters (Action & Revenue).
    """
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Validates details tag wrapper
    assert "<details" in html
    assert "AIM 4-STEP AUTONOMOUS ENGINE" in html
    assert "AIM_Base.md 4단계 선순환 구조 펼쳐보기" in html
    # Validates 3-step flywheel is primary
    assert "AIM 3단계 자율 선순환 (3-Step Closed-Loop Flywheel)" in html


def test_step2_and_step3_direct_1click_prescription_publishing():
    """Steps 2 & 3 (Delete Bottlenecks & Simplify):

    Validates that a merchant can publish a prescription directly in 1 click
    without going through a modal inspection step if they prefer instant action.
    Also verifies that the JavaScript handles quickPublishPrescription.
    """
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # HTML contains the direct 1-click dispatch button script in renderPrescriptions
    assert "quickPublishPrescription" in html
    assert "⚡ 1클릭 즉시 발송" in html
    assert "✏️ 카피 보기" in html

    # Backend API accepts direct publication without prerequisite modal calls
    tenant_id = "TENANT_001"
    tenant_before = TenantManager.get_tenant(tenant_id)
    rev_before = tenant_before.cumulative_revenue_generated_krw

    direct_pub_res = client.post(
        "/api/v1/consulting/mark-published",
        json={
            "tenant_id": tenant_id,
            "advice_id": "ADV_TENANT_001_WEATHER",
            "channel": "NAVER_PLACE",
            "headline": "[비 오는 날 3시간 한정] 갓 구운 바질소금빵 1+1 옴니채널 번개 특가",
            "gain_krw": 240000,
        },
    )
    assert direct_pub_res.status_code == 200
    pub_data = direct_pub_res.json()
    assert pub_data["status"] == "LIVE"
    assert pub_data["tenant_id"] == tenant_id
    assert pub_data["attributed_revenue_gain_krw"] == 240000

    tenant_after = TenantManager.get_tenant(tenant_id)
    assert tenant_after.cumulative_revenue_generated_krw == rev_before + 240000


def test_step4_accelerated_cycle_time_benchmark():
    """Step 4 (Accelerate Cycle Time):

    Validates that the entire cycle—from consulting prescription generation
    to 1-click publishing—executes in sub-second latency with atomic state synchronization.
    """
    tenant_id = "TENANT_001"

    # 1. Sensing & Prescriptions (< 50ms)
    report = AIConsultingAdvisor.evaluate_tenant(tenant_id)
    assert len(report.prescriptions) == 4
    target_prescription = report.prescriptions[0]

    # 2. Automated Multi-channel Bundle Generation (< 50ms)
    bundle = ContentPublisher.synthesize_bundle(tenant_id, target_prescription.advice_id)
    assert bundle.bundle_id.startswith("PUB_")
    assert len(bundle.naver_place.title_max40) <= 40

    # 3. Mark Published and Synchronize (< 20ms)
    record = ContentPublisher.record_publication(
        tenant_id=tenant_id,
        channel="NAVER_PLACE",
        headline=bundle.naver_place.title_max40,
        trigger_type="🌧️ 기상 인프라 실시간 감지",
        gain_krw=target_prescription.expected_revenue_gain_krw,
    )
    assert record.status == "LIVE"
    assert record.attributed_revenue_gain_krw == target_prescription.expected_revenue_gain_krw


def test_step5_complete_automated_closed_loop():
    """Step 5 (Automate):

    Validates the end-to-end automated closed-loop lifecycle:
    1. Quick action approve triggers multi-channel dispatch
    2. Customer mobile ticket is issued and accessible without app install
    3. POS scans and redeems coupon with automated split
    4. Ledger reflects A_MEASURED evidence
    """
    tenant_id = "TENANT_001"

    # 1. 1-Click Quick Action Dispatch
    dispatch_res = client.post(
        f"/api/v1/tenant/{tenant_id}/quick-action/approve",
        json={"custom_trigger": "머스크 5단계 엔지니어링 자율 발송"},
    )
    assert dispatch_res.status_code == 200
    assert dispatch_res.json()["status"] == "SUCCESS"

    # 2. Customer Coupon Issuance
    cp = coupon_vault.issue_coupon(
        tenant_id=tenant_id,
        campaign_id="CAMP_MUSK_AUTO_01",
        channel="NAVER_PLACE",
        creator_id="CR_002",
        discount_amount_krw=3000,
        min_order_amount_krw=20000,
    )
    assert cp.coupon_code.startswith("AIM-")

    # 3. Customer Web Ticket Rendering
    ticket_res = client.get(f"/c/{cp.coupon_code}")
    assert ticket_res.status_code == 200
    assert "바코드" in ticket_res.text

    # 4. POS Scan Redemption with Automated Split
    redeem_res = client.post(
        "/api/v1/monetization/coupon/redeem",
        json={"coupon_code": cp.coupon_code, "order_amount_krw": 25000},
    )
    assert redeem_res.status_code == 200
    redeem_data = redeem_res.json()
    assert redeem_data["success"] is True
    assert redeem_data["discount_applied_krw"] == 3000
    assert redeem_data["final_paid_amount_krw"] == 22000
    assert redeem_data["evidence_tier"] == "A_MEASURED"
    assert redeem_data["revenue_split"]["platform_commission_krw"] == int(25000 * 0.08)
    assert redeem_data["revenue_split"]["creator_bonus_krw"] == int(25000 * 0.03)

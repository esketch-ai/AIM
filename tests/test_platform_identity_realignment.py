"""Tests for Platform Identity Realignment & Foundational Specs Compliance
(tests/test_platform_identity_realignment.py)
-------------------------------------------------------------------------
Validates:
1. Core platform title and authentic killer slogan aligned with AIM_Base.md
2. 4-step autonomous marketing OS cyclical engine presence in template
3. 5-industry tenant switcher in clean minimalist view
4. Multi-industry quick action approval support across all 5 tenants
5. Elimination of local restaurant discount coupon bias as platform identity
"""

import pytest
from fastapi.testclient import TestClient

from aim.web_app import app
from aim.tenant.manager import TenantManager

client = TestClient(app)


def test_core_platform_identity_in_rendered_html():
    """Validates that rendered HTML reflects AIM_Base.md identity and authentic slogan."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Page Title & Brand Slogan
    assert "AIM Marketing OS — 사업장 데이터 기반 자율 마케팅 운영체제" in html
    assert "내 사업장 데이터만 연결하면, AI가 5대 채널 마케팅을 알아서 끝냅니다." in html
    assert "AIM · 자율 마케팅 OS" in html

    # 2. AIM_Base.md 4-Step Cyclical Engine
    assert "AIM 4-STEP AUTONOMOUS ENGINE" in html
    assert "1단계: 데이터 자동 연결" in html
    assert "2단계: 5대 채널 자동 분기" in html
    assert "3단계: 법적 검수·원클릭 승인" in html
    assert "4단계: 매출 증명·자율 학습" in html

    # 3. 5-Industry Switcher in Clean Mode
    assert "sBtn_TENANT_001" in html
    assert "sBtn_TENANT_002" in html
    assert "sBtn_TENANT_003" in html
    assert "sBtn_TENANT_004" in html
    assert "sBtn_TENANT_005" in html


@pytest.mark.parametrize("tenant_id, expected_domain", [
    ("TENANT_001", "fnb"),
    ("TENANT_002", "medical"),
    ("TENANT_003", "beauty"),
    ("TENANT_004", "b2b_saas"),
    ("TENANT_005", "manufacturing"),
])
def test_all_five_industry_tenants_quick_action(tenant_id, expected_domain):
    """Validates that all 5 industry tenants can execute 1-click quick action with their own trigger."""
    tenant = TenantManager.get_tenant(tenant_id)
    assert tenant is not None
    assert tenant.domain == expected_domain

    res = client.post(f"/api/v1/tenant/{tenant_id}/quick-action/approve")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["tenant_id"] == tenant_id
    assert tenant.business_name in data["message"]
    assert len(data["dispatched_channels"]) >= 3


def test_no_sole_bias_to_fnb_coupon():
    """Validates that the landing and clean mode support all industries equally."""
    res = client.get("/")
    html = res.text
    # Should contain references to multiple domains
    assert "강남 리엔 피부과" in html
    assert "플로우독 IT" in html or "플로우독 SaaS" in html
    assert "대진정밀공업" in html

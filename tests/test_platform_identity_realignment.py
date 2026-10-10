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


def test_ai_era_webapp_instant_gtm_launcher_in_html():
    """Validates that the AI-Era Web & App Service Instant GTM Launcher is prominently available."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert "AI-ERA WEB & APP SERVICES GTM DISTRIBUTION OS" in html
    assert "내 웹·앱·SaaS 서비스 URL만 입력하면, 3초 만에 5대 채널 GTM 마케팅 자동 발사" in html
    assert "inputServiceUrl" in html
    assert "handleInstantServiceLaunch" in html
    assert "presetServiceLaunch" in html
    assert "플로우독 AI 협업툴 (SaaS 웹앱)" in html


def test_customer_development_14_rules_framework_in_html():
    """Validates that Steve Blank's 14 Customer Development Principles framework is prominently delivered to new founders."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Framework Identity & Manifesto OS
    assert "고객 개발 14대 원칙" in html
    assert "Customer Development" in html
    assert "CUSTOMER DEVELOPMENT MANIFESTO OS" in html
    assert "신규 사업자를 위한 고객 개발 14대 원칙 체계" in html

    # 2. 4 Practical Stages for New Founders
    assert "고객 발견 (Customer Discovery)" in html
    assert "고객 검증 (Customer Validation)" in html
    assert "고객 창출 (Customer Creation)" in html
    assert "사업 빌딩 & 피벗 (Company Building & Pivot)" in html

    # 3. Steve Blank Key Principles
    assert "사무실에서 알 수 있는 것은 없으니 현장으로 나가라" in html
    assert "고객 개발에 애자일 개발을 접목하라" in html
    assert "실패는 탐색 절차의 필수적인 요소다" in html
    assert "비즈니스 모델 캔버스" in html
    assert "스타트업은 기존 기업과 다른 지표를 쓴다" in html
    assert "필요할 때만 쓰고 아껴라" in html

    # 4. Interactive Modal & Handlers
    assert "openCustomerDevelopmentModal" in html
    assert "customerDevModal" in html
    assert "triggerCustomerDevPhase" in html
    assert "실리콘밸리 고객 개발 14대 원칙(Customer Development Manifesto) 내장 온보딩" in html


def test_step_by_step_guided_stepper_in_html():
    """Validates that the main page features a concise, step-by-step progressive disclosure flow."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Stepper Navigator & Step Tabs
    assert "STEP-BY-STEP PROGRESSIVE GUIDANCE" in html
    assert "하나씩 차근차근 알아가는 3단계 자율 마케팅 여정" in html
    assert "stepTabBtn1" in html
    assert "stepTabBtn2" in html
    assert "stepTabBtn3" in html
    assert "1단계: 내 비즈니스 연결" in html
    assert "2단계: AI 진단 & 오늘 할 일" in html
    assert "3단계: 배포 & 매출 증명" in html

    # 2. Step Containers
    assert 'id="stepContainer1"' in html
    assert 'id="stepContainer2"' in html
    assert 'id="stepContainer3"' in html

    # 3. Stepper Controller Functions
    assert "goToStep" in html
    assert "toggleStepperMode" in html
    assert "currentStepIndicatorBadge" in html




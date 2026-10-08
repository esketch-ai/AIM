"""
AIM Master Admin Control Plane & FinOps War Room — Granular Unit Tests
----------------------------------------------------------------------
Very granular and comprehensive test suite validating all detailed attributes of Solution 3:
1. TestMasterAdminKpisGranular (MRR, Value, ROI formulas, zero-division safety, uptime)
2. TestFleetLifecycleAndStatusGranular (ACTIVE/PAUSED/SUSPENDED, FREE/PRO/ENTERPRISE tier changes)
3. TestFleetFinOpsMetricsGranular (ARR = 12x MRR, ARPU, domain & tier distributions)
4. TestFleetOnboardingGranular (Tenant provisioning, duplicate ID prevention, initial invoice)
5. TestComplianceQuarantineHITLGranular (Medical/Fair advertising risk, Human-in-the-Loop review notes, timestamps)
6. TestComplianceAuditTrailGranular (Chronological intercept logging, domain-specific filtering)
7. TestDistributedAgentTelemetryGranular (AI worker latency, health check status schema)
8. TestAdminRestApiEndpointsGranular (FastAPI REST contract E2E, 200 OK, 400 & 404 error cases)
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from aim.schema import PlatformMasterKPI, ComplianceAuditLogEntry, TenantAccount
from aim.admin.master_console import MasterAdminConsole
from aim.admin.quarantine import ComplianceQuarantineQueue, QuarantinedItem
from aim.admin.fleet import FleetController, FleetMetrics, OnboardTenantRequest
from aim.tenant.manager import TenantManager
from aim.tenant.billing import BillingService
from aim.web_app import app

client = TestClient(app)


class TestMasterAdminKpisGranular:
    """Validates mathematical and logical precision of Global Platform KPIs."""

    def setup_method(self):
        TenantManager._initialize_defaults()
        MasterAdminConsole.reset_defaults()

    def test_kpi_calculation_with_active_fleet(self):
        kpis = MasterAdminConsole.get_global_kpis()
        assert isinstance(kpis, PlatformMasterKPI)
        assert kpis.total_active_tenants >= 5
        assert kpis.total_mrr_krw >= 545000
        assert kpis.total_platform_value_krw > 100000000
        assert kpis.average_roi_multiplier > 0.0
        assert kpis.system_uptime_percent == 99.98
        assert kpis.total_compliance_blocks >= 4

    def test_kpi_mrr_recalculation_on_tenant_pause(self):
        initial_kpis = MasterAdminConsole.get_global_kpis()
        initial_mrr = initial_kpis.total_mrr_krw
        initial_active = initial_kpis.total_active_tenants

        # Pause TENANT_001 (PRO, 49,000 KRW)
        TenantManager.update_status("TENANT_001", "PAUSED")
        paused_kpis = MasterAdminConsole.get_global_kpis()

        assert paused_kpis.total_active_tenants == initial_active - 1
        assert paused_kpis.total_mrr_krw == initial_mrr - 49000

        # Restore TENANT_001
        TenantManager.update_status("TENANT_001", "ACTIVE")
        restored_kpis = MasterAdminConsole.get_global_kpis()
        assert restored_kpis.total_mrr_krw == initial_mrr
        assert restored_kpis.total_active_tenants == initial_active

    def test_kpi_roi_formula_zero_division_safety(self):
        # Temporarily set all tenants to PAUSED to simulate 0 MRR
        tenants = TenantManager.list_tenants()
        for t in tenants:
            t.status = "PAUSED"

        zero_mrr_kpis = MasterAdminConsole.get_global_kpis()
        assert zero_mrr_kpis.total_mrr_krw == 0
        assert zero_mrr_kpis.average_roi_multiplier == 0.0

        # Restore tenants
        for t in tenants:
            t.status = "ACTIVE"

    def test_kpi_compliance_blocks_count_sync(self):
        initial_blocks = MasterAdminConsole.get_global_kpis().total_compliance_blocks
        MasterAdminConsole.record_audit_intercept(
            tenant_id="TENANT_001",
            business_name="성수 아뜰리에",
            domain="fnb",
            intercepted_term="세계 최고 빵집",
            rule_category="표시광고법",
            sanitized_to="자부심 있는 인기 빵집",
        )
        updated_blocks = MasterAdminConsole.get_global_kpis().total_compliance_blocks
        assert updated_blocks == initial_blocks + 1


class TestFleetLifecycleAndStatusGranular:
    """Validates tenant lifecycle state machine and subscription tier changes."""

    def setup_method(self):
        TenantManager._initialize_defaults()

    def test_tenant_status_transition_active_to_paused(self):
        tenant = TenantManager.update_status("TENANT_003", "PAUSED")
        assert tenant is not None
        assert tenant.status == "PAUSED"
        refetched = TenantManager.get_tenant("TENANT_003")
        assert refetched.status == "PAUSED"

    def test_tenant_status_transition_paused_to_active(self):
        tenant = TenantManager.update_status("TENANT_003", "ACTIVE")
        assert tenant is not None
        assert tenant.status == "ACTIVE"

    def test_tenant_status_invalid_tenant_returns_none(self):
        res = TenantManager.update_status("TENANT_NON_EXISTENT_999", "ACTIVE")
        assert res is None

    def test_tenant_plan_upgrade_pro_to_enterprise(self):
        tenant = TenantManager.get_tenant("TENANT_001")
        assert tenant.subscription_tier == "PRO"
        assert tenant.monthly_fee_krw == 49000

        # Upgrade to ENTERPRISE
        upgraded = TenantManager.update_subscription_tier("TENANT_001", "ENTERPRISE")
        assert upgraded.subscription_tier == "ENTERPRISE"
        assert upgraded.monthly_fee_krw == 199000

        # Verify global MRR reflects the 150,000 KRW jump
        kpis = MasterAdminConsole.get_global_kpis()
        assert kpis.total_mrr_krw >= 695000

        # Restore to PRO
        restored = TenantManager.update_subscription_tier("TENANT_001", "PRO")
        assert restored.subscription_tier == "PRO"
        assert restored.monthly_fee_krw == 49000

    def test_tenant_plan_downgrade_to_free(self):
        downgraded = TenantManager.update_subscription_tier("TENANT_001", "FREE")
        assert downgraded.subscription_tier == "FREE"
        assert downgraded.monthly_fee_krw == 0

        # Restore
        TenantManager.update_subscription_tier("TENANT_001", "PRO")


class TestFleetFinOpsMetricsGranular:
    """Validates precision of SaaS FinOps metrics (ARR, ARPU, Distributions)."""

    def setup_method(self):
        TenantManager._initialize_defaults()

    def test_arr_calculation_is_exact_12x_mrr(self):
        metrics = FleetController.get_fleet_metrics()
        assert isinstance(metrics, FleetMetrics)
        assert metrics.annual_run_rate_arr_krw == metrics.total_mrr_krw * 12

    def test_arpu_calculation_is_mrr_divided_by_active(self):
        metrics = FleetController.get_fleet_metrics()
        expected_arpu = int(metrics.total_mrr_krw / metrics.active_tenants)
        assert metrics.average_revenue_per_user_arpu_krw == expected_arpu

    def test_domain_distribution_mapping(self):
        metrics = FleetController.get_fleet_metrics()
        domains = metrics.domain_distribution
        assert "fnb" in domains
        assert "medical" in domains
        assert "beauty" in domains
        assert "b2b_saas" in domains
        assert "manufacturing" in domains
        assert sum(domains.values()) == metrics.total_tenants

    def test_tier_distribution_mapping(self):
        metrics = FleetController.get_fleet_metrics()
        tiers = metrics.tier_distribution
        assert "PRO" in tiers
        assert "ENTERPRISE" in tiers
        assert sum(tiers.values()) == metrics.total_tenants

    def test_platform_overall_roi_metric(self):
        metrics = FleetController.get_fleet_metrics()
        assert metrics.platform_overall_roi > 0.0


class TestFleetOnboardingGranular:
    """Validates complete attribute onboarding of new subscriber businesses."""

    def setup_method(self):
        TenantManager._initialize_defaults()

    def test_onboard_new_tenant_full_attributes(self):
        req = OnboardTenantRequest(
            tenant_id="TENANT_PANGYO_BIO",
            business_name="판교 바이오랩",
            owner_name="정박사",
            domain="medical",
            subscription_tier="ENTERPRISE",
            location="경기 성남시 분당구 판교이노밸리",
            target_audience="글로벌 신약개발 연구소 및 임상기관",
            core_usps=["AI 단백질 폴딩 타겟 분석", "FDA IND 패스트트랙 지원"],
            unit_price=30000000,
            trigger_event="신규 타겟 분자 발굴 보도자료 배포",
        )
        account = FleetController.onboard_new_tenant(req)
        assert account.tenant_id == "TENANT_PANGYO_BIO"
        assert account.business_name == "판교 바이오랩"
        assert account.subscription_tier == "ENTERPRISE"
        assert account.monthly_fee_krw == 199000
        assert account.status == "ACTIVE"
        assert account.business_state.location == "경기 성남시 분당구 판교이노밸리"

        # Verify in TenantManager registry
        fetched = TenantManager.get_tenant("TENANT_PANGYO_BIO")
        assert fetched is not None
        assert fetched.owner_name == "정박사"

        # Verify initial invoice was generated
        invoices = BillingService.get_tenant_invoices("TENANT_PANGYO_BIO")
        assert len(invoices) >= 1
        assert invoices[0].amount_krw == 199000

    def test_onboard_duplicate_tenant_rejection(self):
        req = OnboardTenantRequest(
            tenant_id="TENANT_001",  # Already exists!
            business_name="중복 시도 베이커리",
            owner_name="김중복",
            domain="fnb",
            subscription_tier="PRO",
            location="서울 성수동",
            target_audience="MZ",
            core_usps=["소금빵"],
            unit_price=20000,
            trigger_event="비",
        )
        with pytest.raises(ValueError, match="already exists"):
            FleetController.onboard_new_tenant(req)

    def test_onboard_empty_business_name_rejection(self):
        req = OnboardTenantRequest(
            tenant_id="TENANT_EMPTY_NAME",
            business_name="   ",  # Invalid empty name
            owner_name="홍길동",
            domain="fnb",
            subscription_tier="PRO",
            location="서울",
            target_audience="MZ",
            core_usps=["단팥빵"],
            unit_price=10000,
            trigger_event="날씨",
        )
        with pytest.raises(ValueError, match="business_name cannot be empty"):
            FleetController.onboard_new_tenant(req)


class TestComplianceQuarantineHITLGranular:
    """Validates Human-in-the-Loop review queue, evidence tracking, and review timestamps."""

    def setup_method(self):
        ComplianceQuarantineQueue.reset_defaults()

    def test_quarantine_default_items_and_attributes(self):
        items = ComplianceQuarantineQueue.list_quarantined()
        assert len(items) >= 2

        q1 = ComplianceQuarantineQueue.get_item("Q_101")
        assert q1 is not None
        assert q1.domain == "medical"
        assert q1.risk_level == "CRITICAL"
        assert "의료법" in q1.rule_authority
        assert "부작용 전혀 없음" in q1.flagged_copy
        assert "심의필" in q1.recommended_sanitized
        assert q1.status == "PENDING"
        assert q1.reviewed_at is None

    def test_quarantine_resolve_approved_by_admin(self):
        resolved = ComplianceQuarantineQueue.resolve_item(
            item_id="Q_101",
            decision="APPROVED_BY_ADMIN",
            reviewer="수석 법무관 김준호",
            notes="부작용 주의 문구 및 심의필 번호 확인 후 조건부 승인",
        )
        assert resolved is not None
        assert resolved.status == "APPROVED_BY_ADMIN"
        assert resolved.admin_reviewer == "수석 법무관 김준호"
        assert "조건부 승인" in resolved.review_notes
        assert resolved.reviewed_at is not None

        # Verify persistence on refetch
        refetched = ComplianceQuarantineQueue.get_item("Q_101")
        assert refetched.status == "APPROVED_BY_ADMIN"

    def test_quarantine_resolve_rejected(self):
        resolved = ComplianceQuarantineQueue.resolve_item(
            item_id="Q_102",
            decision="REJECTED",
            reviewer="표시광고 심의관",
            notes="국내 1위 허위 표시로 인한 영구 송출 차단",
        )
        assert resolved is not None
        assert resolved.status == "REJECTED"
        assert resolved.admin_reviewer == "표시광고 심의관"

    def test_quarantine_filter_by_status(self):
        # Initially both Q_101 and Q_102 are PENDING
        pending_items = ComplianceQuarantineQueue.list_quarantined(status_filter="PENDING")
        assert len(pending_items) == 2

        # Resolve Q_101
        ComplianceQuarantineQueue.resolve_item("Q_101", "APPROVED_BY_ADMIN")

        # Check pending filter now only returns 1
        pending_after = ComplianceQuarantineQueue.list_quarantined(status_filter="PENDING")
        assert len(pending_after) == 1
        assert pending_after[0].item_id == "Q_102"

        # Check approved filter
        approved_items = ComplianceQuarantineQueue.list_quarantined(status_filter="APPROVED_BY_ADMIN")
        assert len(approved_items) == 1
        assert approved_items[0].item_id == "Q_101"

    def test_quarantine_resolve_nonexistent_item_returns_none(self):
        resolved = ComplianceQuarantineQueue.resolve_item("Q_NONEXISTENT", "REJECTED")
        assert resolved is None


class TestComplianceAuditTrailGranular:
    """Validates chronological regulatory audit logging and domain-specific filtering."""

    def setup_method(self):
        MasterAdminConsole.reset_defaults()

    def test_audit_log_record_intercept_new_entry(self):
        initial_logs = MasterAdminConsole.get_audit_logs()
        initial_count = len(initial_logs)

        MasterAdminConsole.record_audit_intercept(
            tenant_id="TENANT_002",
            business_name="강남 리엔 피부과",
            domain="medical",
            intercepted_term="100% 완치 보장",
            rule_category="의료법 제56조",
            sanitized_to="맞춤 진단 후 시술",
        )

        updated_logs = MasterAdminConsole.get_audit_logs()
        assert len(updated_logs) == initial_count + 1
        newest = updated_logs[0]
        assert newest.domain == "medical"
        assert newest.intercepted_term == "100% 완치 보장"
        assert newest.sanitized_to == "맞춤 진단 후 시술"
        assert newest.severity == "HIGH"

    def test_audit_log_domain_filtering(self):
        medical_logs = MasterAdminConsole.get_audit_logs(domain="medical")
        assert len(medical_logs) >= 1
        assert all(log.domain == "medical" for log in medical_logs)

        fnb_logs = MasterAdminConsole.get_audit_logs(domain="fnb")
        assert len(fnb_logs) >= 1
        assert all(log.domain == "fnb" for log in fnb_logs)

        mfg_logs = MasterAdminConsole.get_audit_logs(domain="manufacturing")
        assert len(mfg_logs) >= 1
        assert all(log.domain == "manufacturing" for log in mfg_logs)

    def test_audit_log_fields_integrity(self):
        logs = MasterAdminConsole.get_audit_logs()
        for log in logs:
            assert isinstance(log, ComplianceAuditLogEntry)
            assert log.log_id.startswith("LOG_")
            assert log.tenant_id.startswith("TENANT_")
            assert len(log.intercepted_term) > 0
            assert len(log.sanitized_to) > 0


class TestDistributedAgentTelemetryGranular:
    """Validates health check and latency status dictionary of distributed AI workers."""

    def test_agent_worker_status_schema(self):
        kpis = MasterAdminConsole.get_global_kpis()
        workers = kpis.agent_worker_status
        assert "Context Sensing Engine" in workers
        assert "Strategy Decision Engine" in workers
        assert "Multi-Domain Compliance Guard" in workers
        assert "Omni-Channel Synthesis" in workers
        assert "Attribution Feedback Loop" in workers
        assert "정상" in workers["Context Sensing Engine"]
        assert "ms" in workers["Strategy Decision Engine"]


class TestAdminRestApiEndpointsGranular:
    """Validates REST API endpoints under /api/v1/admin with 200 OK and error cases."""

    def setup_method(self):
        TenantManager._initialize_defaults()
        ComplianceQuarantineQueue.reset_defaults()
        MasterAdminConsole.reset_defaults()

    def test_api_get_overview(self):
        res = client.get("/api/v1/admin/overview")
        assert res.status_code == 200
        data = res.json()
        assert "kpis" in data
        assert "tenants" in data
        assert "audit_logs" in data
        assert "quarantine_summary" in data
        assert data["quarantine_summary"]["total_flagged"] >= 2
        assert data["quarantine_summary"]["pending_review"] >= 1

    def test_api_get_fleet_tenants(self):
        res = client.get("/api/v1/admin/tenants")
        assert res.status_code == 200
        tenants = res.json()["tenants"]
        assert len(tenants) >= 5
        tenant_ids = [t["tenant_id"] for t in tenants]
        assert "TENANT_001" in tenant_ids
        assert "TENANT_002" in tenant_ids

    def test_api_post_tenant_status_success_and_404(self):
        # 1. Success
        res_ok = client.post(
            "/api/v1/admin/tenant/status",
            json={"tenant_id": "TENANT_001", "status": "PAUSED"},
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["tenant"]["status"] == "PAUSED"

        # Restore
        client.post(
            "/api/v1/admin/tenant/status",
            json={"tenant_id": "TENANT_001", "status": "ACTIVE"},
        )

        # 2. 404 for unknown tenant
        res_404 = client.post(
            "/api/v1/admin/tenant/status",
            json={"tenant_id": "TENANT_UNKNOWN_404", "status": "ACTIVE"},
        )
        assert res_404.status_code == 404

    def test_api_post_tenant_plan_success_and_404(self):
        # 1. Success
        res_ok = client.post(
            "/api/v1/admin/tenant/plan",
            json={"tenant_id": "TENANT_001", "tier": "ENTERPRISE"},
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["tenant"]["subscription_tier"] == "ENTERPRISE"
        assert res_ok.json()["tenant"]["monthly_fee_krw"] == 199000

        # Restore
        client.post(
            "/api/v1/admin/tenant/plan",
            json={"tenant_id": "TENANT_001", "tier": "PRO"},
        )

        # 2. 404 for unknown tenant
        res_404 = client.post(
            "/api/v1/admin/tenant/plan",
            json={"tenant_id": "TENANT_UNKNOWN_404", "tier": "PRO"},
        )
        assert res_404.status_code == 404

    def test_api_get_quarantine_with_filter(self):
        # 1. Without filter
        res = client.get("/api/v1/admin/quarantine")
        assert res.status_code == 200
        assert len(res.json()["items"]) >= 2

        # 2. With status=PENDING filter
        res_pending = client.get("/api/v1/admin/quarantine?status=PENDING")
        assert res_pending.status_code == 200
        assert all(item["status"] == "PENDING" for item in res_pending.json()["items"])

    def test_api_post_quarantine_resolve_success_and_404(self):
        # 1. Success
        res = client.post(
            "/api/v1/admin/quarantine/Q_101/resolve",
            json={
                "decision": "APPROVED_BY_ADMIN",
                "reviewer": "법무팀장",
                "notes": "심의필 문구 삽입 완료",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["resolved_item"]["status"] == "APPROVED_BY_ADMIN"
        assert data["resolved_item"]["admin_reviewer"] == "법무팀장"

        # 2. 404 for unknown item
        res_404 = client.post(
            "/api/v1/admin/quarantine/Q_9999_NONEXISTENT/resolve",
            json={"decision": "REJECTED"},
        )
        assert res_404.status_code == 404

    def test_api_get_audit_logs_with_domain_filter(self):
        # 1. Without filter
        res = client.get("/api/v1/admin/audit-logs")
        assert res.status_code == 200
        assert len(res.json()["audit_logs"]) >= 4

        # 2. Filter by domain=medical
        res_med = client.get("/api/v1/admin/audit-logs?domain=medical")
        assert res_med.status_code == 200
        logs = res_med.json()["audit_logs"]
        assert len(logs) >= 1
        assert all(log["domain"] == "medical" for log in logs)

    def test_api_get_fleet_metrics(self):
        res = client.get("/api/v1/admin/fleet/metrics")
        assert res.status_code == 200
        m = res.json()
        assert m["total_tenants"] >= 5
        assert m["total_mrr_krw"] >= 545000
        assert m["annual_run_rate_arr_krw"] == m["total_mrr_krw"] * 12
        assert "fnb" in m["domain_distribution"]
        assert "PRO" in m["tier_distribution"]

    def test_api_post_fleet_onboard_success_and_duplicate_400(self):
        # 1. Success
        payload = {
            "tenant_id": "TENANT_API_TEST_01",
            "business_name": "성수 오리지널 베이글",
            "owner_name": "박대표",
            "domain": "fnb",
            "subscription_tier": "PRO",
            "location": "서울 성수동 연무장길",
            "target_audience": "2030 직장인",
            "core_usps": ["유기농 밀가루 100% 당일 베이글"],
            "unit_price": 6000,
            "trigger_event": "출근길 아침 타임어택",
        }
        res = client.post("/api/v1/admin/fleet/onboard", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "SUCCESS"
        assert res.json()["tenant"]["tenant_id"] == "TENANT_API_TEST_01"

        # 2. Re-onboarding same ID returns 400
        res_dup = client.post("/api/v1/admin/fleet/onboard", json=payload)
        assert res_dup.status_code == 400
        assert "already exists" in res_dup.json()["detail"]

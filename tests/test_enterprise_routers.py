"""Tests for AIM Decoupled Enterprise Routers
Validates REST API contracts across:
- Solution 1: Core Service Engine (/api/v1/service/*)
- Solution 2: Subscriber Tenant Portal (/api/v1/tenant/*)
- Solution 3: Platform Master Admin Control Plane (/api/v1/admin/*)
"""

import unittest
from fastapi.testclient import TestClient
from aim.web_app import app


class TestEnterpriseRouters(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # --- Solution 1: Service Engine Tests ---
    def test_service_router_industries_and_simulate(self):
        # 1. List industries
        res = self.client.get("/api/v1/service/industries")
        self.assertEqual(res.status_code, 200)
        self.assertIn("industries", res.json())
        self.assertGreaterEqual(len(res.json()["industries"]), 5)

        # 2. Get specific industry profile
        res_ind = self.client.get("/api/v1/service/industries/medical_derma")
        self.assertEqual(res_ind.status_code, 200)
        self.assertEqual(res_ind.json()["id"], "medical_derma")

        # 3. Simulate dynamic context
        sim_payload = {
            "industry_id": "fnb_cafe",
            "custom_context": {"weather_event": "비 예보", "idle_tables": 8},
        }
        res_sim = self.client.post("/api/v1/service/simulate", json=sim_payload)
        self.assertEqual(res_sim.status_code, 200)
        self.assertIn("simulated_actions", res_sim.json())

    def test_service_router_intelligence(self):
        res = self.client.get("/api/v1/service/intelligence?store_name=성수 아뜰리에 베이커리")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("competitors", data)
        self.assertIn("flash_booster", data)
        self.assertIn("ranking_diagnosis", data)

    # --- Solution 2: Tenant Portal Tests ---
    def test_tenant_router_workflow(self):
        # 1. List tenants
        res = self.client.get("/api/v1/tenant/list")
        self.assertEqual(res.status_code, 200)
        tenants = res.json()["tenants"]
        self.assertGreaterEqual(len(tenants), 5)

        # 2. Get tenant workspace dashboard
        t_res = self.client.get("/api/v1/tenant/TENANT_001")
        self.assertEqual(t_res.status_code, 200)
        t_data = t_res.json()
        self.assertEqual(t_data["tenant"]["tenant_id"], "TENANT_001")
        self.assertIn("live_plan", t_data)
        self.assertIn("financial_summary", t_data)
        self.assertIn("recent_invoices", t_data)

        # 3. Execute campaign from tenant desk
        exec_payload = {"tenant_id": "TENANT_001"}
        exec_res = self.client.post("/api/v1/tenant/execute", json=exec_payload)
        self.assertEqual(exec_res.status_code, 200)
        exec_data = exec_res.json()
        self.assertEqual(exec_data["status"], "SUCCESS")
        self.assertIn("attribution_record", exec_data)
        self.assertGreater(exec_data["projected_revenue"], 0)

        # 4. View billing & upgrade tier
        bill_res = self.client.get("/api/v1/tenant/TENANT_001/billing")
        self.assertEqual(bill_res.status_code, 200)
        self.assertIn("invoices", bill_res.json())

        up_res = self.client.post(
            "/api/v1/tenant/TENANT_001/billing/upgrade", json={"tier": "ENTERPRISE"}
        )
        self.assertEqual(up_res.status_code, 200)
        self.assertEqual(up_res.json()["status"], "SUCCESS")
        self.assertEqual(up_res.json()["issued_invoice"]["tier"], "ENTERPRISE")

        # Revert back
        self.client.post("/api/v1/tenant/TENANT_001/billing/upgrade", json={"tier": "PRO"})

    # --- Solution 3: Master Admin Tests ---
    def test_admin_router_fleet_and_quarantine(self):
        # 1. Admin overview
        ov_res = self.client.get("/api/v1/admin/overview")
        self.assertEqual(ov_res.status_code, 200)
        ov_data = ov_res.json()
        self.assertIn("kpis", ov_data)
        self.assertIn("quarantine_summary", ov_data)
        self.assertGreater(ov_data["kpis"]["total_mrr_krw"], 0)

        # 2. List fleet tenants
        tenants_res = self.client.get("/api/v1/admin/tenants")
        self.assertEqual(tenants_res.status_code, 200)
        self.assertGreaterEqual(len(tenants_res.json()["tenants"]), 5)

        # 3. Toggle tenant status
        status_res = self.client.post(
            "/api/v1/admin/tenant/status",
            json={"tenant_id": "TENANT_004", "status": "PAUSED"},
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["tenant"]["status"], "PAUSED")

        # Restore status
        self.client.post(
            "/api/v1/admin/tenant/status",
            json={"tenant_id": "TENANT_004", "status": "ACTIVE"},
        )

        # 4. List quarantine queue
        q_res = self.client.get("/api/v1/admin/quarantine")
        self.assertEqual(q_res.status_code, 200)
        items = q_res.json()["items"]
        self.assertGreaterEqual(len(items), 2)

        # 5. Resolve quarantine item
        resolve_res = self.client.post(
            "/api/v1/admin/quarantine/Q_102/resolve",
            json={
                "decision": "APPROVED_BY_ADMIN",
                "reviewer": "법무팀장",
                "notes": "베스트 표현으로 완화 후 승인",
            },
        )
        self.assertEqual(resolve_res.status_code, 200)
        self.assertEqual(
            resolve_res.json()["resolved_item"]["status"], "APPROVED_BY_ADMIN"
        )

        # 6. Compliance audit logs
        logs_res = self.client.get("/api/v1/admin/audit-logs")
        self.assertEqual(logs_res.status_code, 200)
        self.assertGreaterEqual(len(logs_res.json()["audit_logs"]), 4)

    def test_tenant_approval_desk_lifecycle(self):
        # 1. List staged campaigns for TENANT_001
        staged_res = self.client.get("/api/v1/tenant/TENANT_001/staged-campaigns")
        self.assertEqual(staged_res.status_code, 200)
        campaigns = staged_res.json()["campaigns"]
        self.assertGreaterEqual(len(campaigns), 1)

        # 2. Stage a fresh campaign with operational trigger
        stage_req = {"custom_trigger": "오후 16시 단체 예약 취소로 빈 테이블 8석 긴급 발생"}
        new_res = self.client.post("/api/v1/tenant/TENANT_001/stage-campaign", json=stage_req)
        self.assertEqual(new_res.status_code, 200)
        new_camp = new_res.json()["staged_campaign"]
        camp_id = new_camp["campaign_id"]
        self.assertEqual(new_camp["status"], "STAGED")

        # 3. Owner approves and dispatches campaign
        approve_res = self.client.post(
            f"/api/v1/tenant/campaign/{camp_id}/approve",
            json={"selected_channels": ["blog", "social"]},
        )
        self.assertEqual(approve_res.status_code, 200)
        approve_data = approve_res.json()
        self.assertEqual(approve_data["status"], "SUCCESS")
        self.assertIn("attribution_record", approve_data)
        self.assertGreater(approve_data["projected_revenue"], 0)

        # 4. Try re-approving (should fail as already approved)
        re_approve = self.client.post(f"/api/v1/tenant/campaign/{camp_id}/approve", json={})
        self.assertEqual(re_approve.status_code, 400)

    def test_admin_fleet_operations_and_finops(self):
        # 1. Get SaaS FinOps metrics
        metrics_res = self.client.get("/api/v1/admin/fleet/metrics")
        self.assertEqual(metrics_res.status_code, 200)
        m = metrics_res.json()
        self.assertGreaterEqual(m["total_tenants"], 5)
        self.assertGreater(m["total_mrr_krw"], 0)
        self.assertGreater(m["annual_run_rate_arr_krw"], 0)
        self.assertIn("fnb", m["domain_distribution"])
        self.assertIn("PRO", m["tier_distribution"])

        # 2. Onboard a new subscriber tenant
        onboard_payload = {
            "tenant_id": "TENANT_006",
            "business_name": "판교 넥스트 바이오팜",
            "owner_name": "강태훈 대표",
            "domain": "medical",
            "subscription_tier": "ENTERPRISE",
            "location": "경기 성남시 분당구 판교밸리",
            "target_audience": "글로벌 CRO 및 임상시험 의뢰사",
            "core_usps": ["AI 신약 타겟 발굴 플랫폼", "GLP 인증 비임상 데이터베이스"],
            "unit_price": 50000000,
            "trigger_event": "신규 면역항암 파이프라인 IND 승인 완료",
        }
        onboard_res = self.client.post("/api/v1/admin/fleet/onboard", json=onboard_payload)
        self.assertEqual(onboard_res.status_code, 200)
        self.assertEqual(onboard_res.json()["status"], "SUCCESS")

        # Verify newly onboarded tenant is in tenant fleet list
        fleet_res = self.client.get("/api/v1/admin/tenants")
        tenant_ids = [t["tenant_id"] for t in fleet_res.json()["tenants"]]
        self.assertIn("TENANT_006", tenant_ids)


if __name__ == "__main__":
    unittest.main()

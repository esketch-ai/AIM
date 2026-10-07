"""Tests for AIM 3 Organic Platform Solutions
Validates the cohesive interplay between:
1. Service Engine (Service Execution Solution)
2. Tenant Workspace (Paid Subscriber Portal Solution)
3. Master Admin Console (Platform Master Management Solution)
"""

import unittest
from fastapi.testclient import TestClient
from aim.web_app import app
from aim.tenant.manager import TenantManager
from aim.admin.master_console import MasterAdminConsole


class TestOrganicPlatformSolutions(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_solution2_tenant_dashboard_and_roi(self):
        # 1. Retrieve tenant list
        res = self.client.get("/api/tenants")
        self.assertEqual(res.status_code, 200)
        tenants = res.json()["tenants"]
        self.assertGreaterEqual(len(tenants), 5)

        # 2. Get specific tenant dashboard (TENANT_001 F&B)
        t_res = self.client.get("/api/tenant/TENANT_001")
        self.assertEqual(t_res.status_code, 200)
        t_data = t_res.json()
        self.assertEqual(t_data["tenant"]["tenant_id"], "TENANT_001")
        self.assertEqual(t_data["tenant"]["subscription_tier"], "PRO")
        self.assertIn("live_plan", t_data)
        self.assertIn("analytics", t_data)
        self.assertGreater(t_data["analytics"]["cumulative_revenue_krw"], 0)

    def test_solution3_master_admin_overview(self):
        res = self.client.get("/api/admin/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        kpis = data["kpis"]
        self.assertGreaterEqual(kpis["total_active_tenants"], 5)
        self.assertGreater(kpis["total_mrr_krw"], 400000)
        self.assertGreater(kpis["total_platform_value_krw"], 50000000)
        self.assertGreater(len(data["audit_logs"]), 0)

    def test_organic_interaction_execution_and_admin_sync(self):
        # Initial admin state
        admin_init = self.client.get("/api/admin/overview").json()
        init_val = admin_init["kpis"]["total_platform_value_krw"]

        # Tenant executes a campaign
        exec_payload = {"tenant_id": "TENANT_003"}  # Beauty Salon
        exec_res = self.client.post("/api/tenant/execute", json=exec_payload)
        self.assertEqual(exec_res.status_code, 200)
        exec_data = exec_res.json()
        self.assertEqual(exec_data["status"], "SUCCESS")
        added_revenue = exec_data["projected_revenue"]
        self.assertGreater(added_revenue, 0)

        # Verify admin console reflects this newly generated value
        admin_updated = self.client.get("/api/admin/overview").json()
        updated_val = admin_updated["kpis"]["total_platform_value_krw"]
        self.assertEqual(updated_val, init_val + added_revenue)

    def test_organic_interaction_admin_plan_upgrade_sync(self):
        # Admin upgrades TENANT_001 from PRO to ENTERPRISE
        upgrade_payload = {"tenant_id": "TENANT_001", "tier": "ENTERPRISE"}
        up_res = self.client.post("/api/admin/tenant/plan", json=upgrade_payload)
        self.assertEqual(up_res.status_code, 200)

        # Check tenant dashboard sees the upgrade
        t_res = self.client.get("/api/tenant/TENANT_001")
        self.assertEqual(t_res.status_code, 200)
        t_data = t_res.json()
        self.assertEqual(t_data["tenant"]["subscription_tier"], "ENTERPRISE")
        self.assertEqual(t_data["tenant"]["monthly_fee_krw"], 199000)

        # Reset back to PRO
        self.client.post("/api/admin/tenant/plan", json={"tenant_id": "TENANT_001", "tier": "PRO"})


if __name__ == "__main__":
    unittest.main()

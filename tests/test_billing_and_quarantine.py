"""Tests for BillingService and ComplianceQuarantineQueue
Verifies billing keys, tier limits, invoice generation, WTP attribution ledger,
and the Human-in-the-Loop quarantine queue.
"""

import unittest
from aim.tenant.billing import BillingService, TIER_CATALOG
from aim.admin.quarantine import ComplianceQuarantineQueue


class TestBillingAndQuarantine(unittest.TestCase):
    def test_tier_catalog(self):
        catalog = BillingService.get_tier_catalog()
        self.assertIn("FREE", catalog)
        self.assertIn("PRO", catalog)
        self.assertIn("ENTERPRISE", catalog)
        self.assertEqual(catalog["FREE"].monthly_fee_krw, 0)
        self.assertEqual(catalog["PRO"].monthly_fee_krw, 49000)
        self.assertEqual(catalog["ENTERPRISE"].monthly_fee_krw, 199000)

    def test_invoice_creation(self):
        inv = BillingService.create_invoice("TENANT_001", "PRO", period="2026-11")
        self.assertEqual(inv.tenant_id, "TENANT_001")
        self.assertEqual(inv.tier, "PRO")
        self.assertEqual(inv.amount_krw, 49000)
        self.assertEqual(inv.status, "PAID")

        invoices = BillingService.get_tenant_invoices("TENANT_001")
        self.assertTrue(any(i.invoice_id == inv.invoice_id for i in invoices))

    def test_attribution_ledger_and_summary(self):
        attr = BillingService.record_attribution(
            tenant_id="TENANT_001",
            campaign_name="테스트 타임어택",
            revenue=500000,
            monthly_fee=49000,
            description="테스트 매출 기여",
        )
        self.assertEqual(attr.tenant_id, "TENANT_001")
        self.assertEqual(attr.generated_revenue_krw, 500000)
        self.assertEqual(attr.net_value_krw, 500000 - 49000)
        self.assertAlmostEqual(attr.roi_multiplier, round(500000 / 49000, 1))

        summary = BillingService.get_financial_summary("TENANT_001", monthly_fee=49000)
        self.assertGreater(summary["total_attributed_revenue_krw"], 0)
        self.assertGreater(summary["overall_roi_multiplier"], 0)

    def test_quarantine_queue_resolution(self):
        items = ComplianceQuarantineQueue.list_quarantined()
        self.assertGreaterEqual(len(items), 2)

        # Get specific item
        item = ComplianceQuarantineQueue.get_item("Q_101")
        self.assertIsNotNone(item)
        self.assertEqual(item.tenant_id, "TENANT_002")

        # Resolve item: Admin conditional approval
        resolved = ComplianceQuarantineQueue.resolve_item(
            item_id="Q_101",
            decision="APPROVED_BY_ADMIN",
            reviewer="수석 법무관",
            notes="안전 문구 삽입 조건부 허용",
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.status, "APPROVED_BY_ADMIN")
        self.assertEqual(resolved.admin_reviewer, "수석 법무관")
        self.assertEqual(resolved.review_notes, "안전 문구 삽입 조건부 허용")

        # Re-fetch item to verify persistence
        refetched = ComplianceQuarantineQueue.get_item("Q_101")
        self.assertEqual(refetched.status, "APPROVED_BY_ADMIN")


if __name__ == "__main__":
    unittest.main()

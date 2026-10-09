"""AIM (AI Platform Initiative) - Multi-Industry Domain Expansion Test Suite (Phase 3)
Verifies:
1. Medical Domain: Medical Law Article 56 guardrails, recall golden-time scheduler, no-show slot fill
2. Beauty Domain: Privacy masking for before/after portfolios, dynamic happy-hour booster, hair cycle recall
3. B2B SaaS Domain: GitHub release to viral 4-channel parser, churn-defense onboarding trigger
4. Precision Manufacturing Domain: 24/7 global RFQ proposal, LME raw material flash deals
5. Auto-quarantine interception for high-risk copies
6. FastAPI endpoints for compliance audit and domain specialized actions
"""

import unittest
from fastapi.testclient import TestClient

from aim.core.compliance_engine import ComplianceEngine
from aim.admin.quarantine import ComplianceQuarantineQueue
from aim.domains.medical import MedicalDomainPlugin
from aim.domains.beauty import BeautyDomainPlugin
from aim.domains.b2b_saas import B2BSaaSDomainPlugin
from aim.domains.manufacturing import ManufacturingDomainPlugin
from aim.web_app import app


class TestMultiIndustryDomainExpansion(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        ComplianceQuarantineQueue.reset_defaults()

    def test_medical_domain_compliance_and_recall(self):
        # 1. Prohibited claims detection under Medical Law Art 56
        violating_text = "우리 피부과는 치료효과 보장 및 재발 제로, 파격 덤핑 할인을 약속드립니다."
        rep = ComplianceEngine.audit(violating_text, domain="medical")
        self.assertFalse(rep.is_compliant)
        violated_terms = [v.original_term for v in rep.violations]
        self.assertIn("치료효과 보장", violated_terms)
        self.assertIn("재발 제로", violated_terms)
        self.assertIn("파격 덤핑 할인", violated_terms)

        # 2. Compliant medical text
        safe_text = "전문의 1:1 맞춤 진단을 통해 정품·정량 원칙을 준수합니다."
        safe_rep = ComplianceEngine.audit(safe_text, domain="medical")
        self.assertTrue(safe_rep.is_compliant)

        # 3. Recall golden-time calculation
        botox_recall = MedicalDomainPlugin.calculate_recall_schedule("botox", 95)
        self.assertTrue(botox_recall["is_golden_time"])
        self.assertFalse(botox_recall["is_overdue"])
        self.assertIn("골든타임", botox_recall["suggested_message"])

        overdue_recall = MedicalDomainPlugin.calculate_recall_schedule("laser", 25)
        self.assertTrue(overdue_recall["is_overdue"])

        # 4. Emergency slot filling
        slot = MedicalDomainPlugin.fill_emergency_slot("강남 리엔 피부과", "15:00", "김원장")
        self.assertIn("15:00", slot["headline"])
        self.assertIn("의료광고 사전심의필", slot["body"])

    def test_beauty_domain_privacy_and_happy_hour(self):
        # 1. Prohibited claims under Fair Advertising
        violating = "우리 살롱은 100% 복구 및 모발 재생 보장, 파격 덤핑으로 시술합니다."
        rep = ComplianceEngine.audit(violating, domain="beauty")
        self.assertFalse(rep.is_compliant)
        violated_terms = [v.original_term for v in rep.violations]
        self.assertIn("100% 복구", violated_terms)
        self.assertIn("모발 재생 보장", violated_terms)

        # 2. Before/After privacy masking
        masked = BeautyDomainPlugin.apply_privacy_masking("김철수", has_before_after=True)
        self.assertEqual(masked["masked_customer_name"], "김*수")
        self.assertEqual(masked["privacy_compliance"], "EYE_BLUR_APPLIED")
        self.assertTrue(masked["consent_verified"])

        # 3. Dynamic happy-hour booster
        booster = BeautyDomainPlugin.generate_happy_hour_booster(
            salon_name="아뜰리에 헤어",
            idle_seats=5,
            target_hours="평일 14:00~17:00",
            free_upgrade="프리미엄 두피 스파",
        )
        self.assertEqual(booster["idle_seats"], 5)
        self.assertIn("해피아워", booster["headline"])
        self.assertIn("5석", booster["incentive"])

        # 4. Hair cycle recall
        cycle = BeautyDomainPlugin.calculate_hair_cycle_recall("cut", 5)
        self.assertTrue(cycle["is_due_for_recall"])
        self.assertIn("커트", cycle["service_name"])

    def test_b2b_saas_release_viral_and_churn_nudge(self):
        # 1. Prohibited claims under GDPR/Data Protection
        violating = "저희 플랫폼은 해킹 100% 원천 차단 및 무결점 보안을 제공합니다."
        rep = ComplianceEngine.audit(violating, domain="b2b_saas")
        self.assertFalse(rep.is_compliant)
        violated = [v.original_term for v in rep.violations]
        self.assertIn("해킹 100% 원천 차단", violated)
        self.assertIn("무결점 보안", violated)

        # 2. GitHub Release Notes parser to 4-channel viral GTM
        release_notes = """
        ## What's Changed
        - feat: Add AI Automated Sprint Retrospective (#104)
        - feat: Real-time GitHub Issue Bi-directional Sync (#105)
        - fix: Fix webhook timeout for enterprise tenants (#106)
        """
        viral = B2BSaaSDomainPlugin.parse_github_release_to_viral(
            product_name="TaskFlow",
            version="v3.2.0",
            release_notes=release_notes,
        )
        self.assertEqual(viral["version"], "v3.2.0")
        self.assertIn("TaskFlow v3.2.0 🚀", viral["product_hunt"]["title"])
        self.assertEqual(len(viral["twitter_thread"]), 3)
        self.assertIn("TaskFlow v3.2.0", viral["linkedin_post"])
        self.assertIn("New Features", viral["changelog"])

        # 3. Churn defense onboarding nudge
        nudge = B2BSaaSDomainPlugin.generate_churn_killer_nudge(
            product_name="TaskFlow",
            user_role="엔지니어링 리드",
            inactive_days=3,
        )
        self.assertIn("엔지니어링 리드", nudge["subject"])
        self.assertEqual(nudge["inactive_days"], 3)

    def test_manufacturing_rfq_and_lme_deal(self):
        # 1. Prohibited claims under Fair Trade / Subcontracting Act
        violating = "당사는 불량률 0% 완전 보장 및 납기 지연 배상 면책 조건으로 공급합니다."
        rep = ComplianceEngine.audit(violating, domain="manufacturing")
        self.assertFalse(rep.is_compliant)
        violated = [v.original_term for v in rep.violations]
        self.assertIn("불량률 0% 완전 보장", violated)
        self.assertIn("납기 지연 배상 면책", violated)

        # 2. 24/7 Global RFQ response generator
        rfq = ManufacturingDomainPlugin.generate_global_rfq_response(
            company_name="한국정밀공업",
            buyer_country="Germany",
            part_name="Robotics Planetary Gear",
            tolerance_spec="±0.003mm",
            certifications=["ISO 9001:2015", "IATF 16949"],
            moq=1000,
            lead_time_days=20,
        )
        self.assertEqual(rfq["buyer_country"], "Germany")
        self.assertEqual(rfq["specifications"]["machining_tolerance"], "±0.003mm")
        self.assertIn("Robotics Planetary Gear", rfq["headline"])

        # 3. LME raw material dip flash deal
        lme_deal = ManufacturingDomainPlugin.generate_lme_raw_material_deal(
            company_name="한국정밀공업",
            material_name="알루미늄 6061",
            price_drop_pct=8.5,
            discount_offer_pct=5.0,
        )
        self.assertIn("8.5%", lme_deal["narrative"])
        self.assertIn("5.0%", lme_deal["narrative"])

    def test_auto_quarantine_interception(self):
        initial_count = len(ComplianceQuarantineQueue.list_quarantined())

        # Audit with auto_quarantine=True
        flagged_text = "환절기 100% 완치 보장 및 부작용 전혀 없음 피부 레이저 특가 이벤트!"
        rep = ComplianceEngine.audit(
            text=flagged_text,
            domain="medical",
            tenant_id="TENANT_MED_001",
            business_name="오라클 메디컬 의원",
            auto_quarantine=True,
        )
        self.assertFalse(rep.is_compliant)

        # Verify queued item
        new_items = ComplianceQuarantineQueue.list_quarantined()
        self.assertEqual(len(new_items), initial_count + 1)

        # Find enqueued item
        new_item = [i for i in new_items if i.tenant_id == "TENANT_MED_001"][0]
        self.assertEqual(new_item.status, "PENDING")
        self.assertEqual(new_item.risk_level, "CRITICAL")
        self.assertIn("100% 완치", new_item.violation_reason)

        # Admin resolves quarantine
        resolved = ComplianceQuarantineQueue.resolve_item(
            item_id=new_item.item_id,
            decision="REJECTED",
            reviewer="시니어 법무팀장",
            notes="의료법 제56조 위반으로 게시 불허",
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.status, "REJECTED")
        self.assertEqual(resolved.admin_reviewer, "시니어 법무팀장")

    def test_api_endpoints_integration(self):
        # 1. POST /api/v1/compliance/audit
        res = self.client.post(
            "/api/v1/compliance/audit",
            json={
                "text": "완벽 개선 및 100% 완치 보장",
                "domain": "medical",
                "auto_quarantine": False,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["is_compliant"])
        self.assertGreater(len(data["violations"]), 0)

        # 2. POST /api/v1/domains/medical/recall-schedule
        res = self.client.post(
            "/api/v1/domains/medical/recall-schedule",
            json={"procedure_type": "botox", "days_since": 90},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["is_golden_time"])

        # 3. POST /api/v1/domains/beauty/happy-hour
        res = self.client.post(
            "/api/v1/domains/beauty/happy-hour",
            json={"salon_name": "청담 살롱", "idle_seats": 4},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["idle_seats"], 4)

        # 4. POST /api/v1/domains/b2b-saas/github-viral
        res = self.client.post(
            "/api/v1/domains/b2b-saas/github-viral",
            json={
                "product_name": "AIM Platform",
                "version": "v1.0.0",
                "release_notes": "feat: 5-channel atomization and AEO/GEO integration",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("AIM Platform v1.0.0", res.json()["product_hunt"]["title"])

        # 5. POST /api/v1/domains/manufacturing/rfq
        res = self.client.post(
            "/api/v1/domains/manufacturing/rfq",
            json={
                "company_name": "한국정밀",
                "buyer_country": "USA",
                "part_name": "Flange Bracket",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["buyer_country"], "USA")


if __name__ == "__main__":
    unittest.main()

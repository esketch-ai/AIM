"""Tests for Multi-Industry 6D Contextual Testbed Engine
Verifies that all 5 industries load properly, execute 6D simulations, and adapt dynamically.
"""

import unittest
from aim.testbed_engine import IndustryTestbedEngine


class TestIndustryTestbedEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IndustryTestbedEngine()

    def test_all_five_industries_loaded(self):
        industries = self.engine.list_industries()
        self.assertEqual(len(industries), 5)
        
        industry_ids = {ind["id"] for ind in industries}
        expected_ids = {
            "fnb_cafe",
            "medical_derma",
            "beauty_salon",
            "b2b_saas",
            "b2b_manufacturing",
        }
        self.assertEqual(industry_ids, expected_ids)

    def test_6d_context_integrity(self):
        for ind_meta in self.engine.list_industries():
            profile = self.engine.get_industry(ind_meta["id"])
            self.assertIsNotNone(profile)
            ctx = profile.context_6d
            self.assertTrue(bool(ctx.era))
            self.assertTrue(bool(ctx.situation))
            self.assertTrue(bool(ctx.season))
            self.assertTrue(bool(ctx.generation))
            self.assertTrue(bool(ctx.region))
            self.assertTrue(bool(ctx.milestone))

            actions = profile.simulated_actions
            self.assertTrue(bool(actions.action_title))
            self.assertTrue(bool(actions.channel_1_blog))
            self.assertTrue(bool(actions.channel_2_insta))
            self.assertTrue(bool(actions.channel_3_direct))
            self.assertTrue(bool(actions.compliance_check))
            self.assertTrue(bool(actions.expected_roi))

    def test_medical_compliance_in_testbed(self):
        med_profile = self.engine.get_industry("medical_derma")
        self.assertIn("의료법 제56조", med_profile.simulated_actions.compliance_check)
        self.assertIn("리엔 피부과의원", med_profile.name)

    def test_b2b_manufacturing_simulation(self):
        mfg_profile = self.engine.get_industry("b2b_manufacturing")
        self.assertIn("창원", mfg_profile.location)
        self.assertIn("RFQ", mfg_profile.simulated_actions.action_title)
        self.assertIn("45,000,000", mfg_profile.simulated_actions.expected_roi)

    def test_dynamic_custom_context_simulation(self):
        # Override situation and season for F&B Cafe
        custom = {
            "situation": "기습 첫눈 및 영하 5도 한파",
            "season": "초겨울 딸기 시즌",
            "milestone": "크리스마스 사전 예약",
        }
        simulated = self.engine.simulate_action("fnb_cafe", custom_context=custom)
        self.assertIn("기습 첫눈 및 영하 5도 한파", simulated.simulated_actions.action_title)
        self.assertIn("초겨울 딸기 시즌", simulated.simulated_actions.channel_2_insta)
        self.assertEqual(simulated.context_6d.situation, "기습 첫눈 및 영하 5도 한파")

    def test_invalid_industry_id(self):
        with self.assertRaises(ValueError):
            self.engine.simulate_action("non_existent_industry")


class TestTestbedAPI(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from aim.web_app import app
        self.client = TestClient(app)

    def test_api_list_industries(self):
        res = self.client.get("/api/testbed/industries")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("industries", data)
        self.assertEqual(len(data["industries"]), 5)

    def test_api_get_industry(self):
        res = self.client.get("/api/testbed/industry/b2b_saas")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "플로우독 (FlowDoc) - AI 협업 툴")
        self.assertIn("온보딩 이탈 방어", data["simulated_actions"]["action_title"])
        self.assertIn("GitHub", data["simulated_actions"]["channel_2_insta"])

    def test_api_get_industry_not_found(self):
        res = self.client.get("/api/testbed/industry/unknown_id")
        self.assertEqual(res.status_code, 404)

    def test_api_simulate(self):
        payload = {
            "industry_id": "beauty_salon",
            "custom_context": {
                "situation": "금요일 저녁 긴급 빈자리",
                "milestone": "주말 소개팅 전날"
            }
        }
        res = self.client.post("/api/testbed/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("금요일 저녁 긴급 빈자리", data["simulated_actions"]["action_title"])


if __name__ == "__main__":
    unittest.main()

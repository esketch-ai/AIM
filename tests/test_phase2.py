"""AIM (AI Platform Initiative) - Phase 2 Verification Tests
Validates URL Ingestion, Reputation Crisis Engine, and Web API Endpoints.
Adheres to Karpathy Principle 3: Verify Obsessively.
"""

import unittest
from fastapi.testclient import TestClient
from aim.url_ingester import StoreUrlIngester
from aim.reputation import ReputationCrisisEngine
from aim.web_app import app


class TestPhase2Features(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_url_ingester_html_parsing(self):
        """Test HTML OpenGraph parsing and metadata extraction without external dependencies."""
        mock_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>을지로 전통 골뱅이 전문점 : 네이버 플레이스</title>
            <meta property="og:title" content="을지로 전통 골뱅이 전문점" />
            <meta property="og:description" content="30년 전통 파채 가득한 원조 골뱅이 무침과 계란말이 서비스. 직장인 회식 명소." />
            <meta property="og:image" content="https://example.com/food.jpg" />
        </head>
        <body></body>
        </html>
        """
        parsed = StoreUrlIngester.parse_html_content(mock_html, "https://m.place.naver.com/restaurant/999")
        self.assertEqual(parsed["name"], "을지로 전통 골뱅이 전문점")
        self.assertIn("30년 전통", parsed["description"])
        self.assertEqual(parsed["category"], "일반음식점")

        raw_data = StoreUrlIngester.build_initial_raw_data(parsed)
        self.assertIn("골뱅이", raw_data.store_info.name)
        self.assertEqual(len(raw_data.pos_summary.top_selling_items), 2)

    def test_reputation_crisis_engine(self):
        """Test 1-star negative review analysis and 3-tier dignified responses."""
        review_text = "음식도 다 식어서 나오고 직원도 너무 불친절해서 최악이었습니다."
        res = ReputationCrisisEngine.generate_dignified_responses(
            store_name="성수 베이커리", review_text=review_text, rating=1.0
        )

        self.assertEqual(res.analysis.rating, 1.0)
        self.assertEqual(res.analysis.sentiment, "CRITICAL_NEGATIVE")
        self.assertIn("불친절", res.analysis.key_issue_phrases)

        # Check all 3 options are generated
        self.assertIn("고개 숙여 사과드립니다", res.option_empathetic)
        self.assertIn("프로세스를 보완하여", res.option_factual)
        self.assertIn("정성을 다해 다시 모시겠습니다", res.option_recovery)
        self.assertTrue(res.compliance_safe)

    def test_web_api_endpoints(self):
        """Test FastAPI endpoints for UI and mobile integration."""
        # 1. Root HTML
        resp_root = self.client.get("/")
        self.assertEqual(resp_root.status_code, 200)
        self.assertIn("AIM Marketing OS", resp_root.text)
        self.assertIn("mobile-frame", resp_root.text)

        # 2. Ingest URL API - collection failure must surface, never mask with mock data
        resp_failed = self.client.post(
            "/api/ingest-url", json={"url": "https://collection-failure-probe.invalid/x"}
        )
        self.assertEqual(resp_failed.status_code, 502)
        failed_data = resp_failed.json()
        self.assertEqual(failed_data["status"], "COLLECTION_FAILED")
        self.assertEqual(failed_data["collection"]["status"], "FAILED")
        self.assertNotIn("channels", failed_data)

        # 2b. Demo mode keeps the illustrative pipeline available for walkthroughs
        resp_demo = self.client.post(
            "/api/ingest-url",
            json={"url": "https://collection-failure-probe.invalid/x", "allow_mock_fallback": True},
        )
        self.assertEqual(resp_demo.status_code, 200)
        data = resp_demo.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("channels", data)
        self.assertIn("naver_blog", data["channels"])
        self.assertEqual(data["pos_evidence_tier"], "C_ILLUSTRATIVE")
        self.assertIn("collection", data)

        # 3. Crisis Response API
        resp_crisis = self.client.post(
            "/api/crisis-response",
            json={"store_name": "성수 테스트점", "review_text": "웨이팅이 너무 길어서 짜증났어요", "rating": 1.0},
        )
        self.assertEqual(resp_crisis.status_code, 200)
        crisis_data = resp_crisis.json()
        self.assertIn("option_empathetic", crisis_data)

        # 4. Approve API
        resp_approve = self.client.post(
            "/api/approve", json={"store_id": "STORE_001", "selected_channels": ["naver_blog"]}
        )
        self.assertEqual(resp_approve.status_code, 200)
        self.assertEqual(resp_approve.json()["status"], "APPROVED")

    def test_tone_switching(self):
        """Test multi-audience tone generation and switching."""
        # 1. MZ Tone check (should contain trendy MZ phrases)
        resp_mz = self.client.post("/api/switch-tone", json={"tone": "MZ_TREND"})
        self.assertEqual(resp_mz.status_code, 200)
        data_mz = resp_mz.json()
        insta_body_mz = data_mz["channels"]["instagram"]["body"]
        self.assertIn("혈중 버터 농도", insta_body_mz)
        self.assertIn("오픈런", insta_body_mz)

        # 2. Worker Healing Tone check
        resp_worker = self.client.post("/api/switch-tone", json={"tone": "WORKER_HEALING"})
        self.assertEqual(resp_worker.status_code, 200)
        data_worker = resp_worker.json()
        insta_body_worker = data_worker["channels"]["instagram"]["body"]
        self.assertIn("퇴근길", insta_body_worker)

        # 3. Local Family Tone check
        resp_family = self.client.post("/api/switch-tone", json={"tone": "LOCAL_FAMILY"})
        self.assertEqual(resp_family.status_code, 200)
        data_family = resp_family.json()
        insta_body_family = data_family["channels"]["instagram"]["body"]
        self.assertIn("우리 가족", insta_body_family)


if __name__ == "__main__":
    unittest.main()

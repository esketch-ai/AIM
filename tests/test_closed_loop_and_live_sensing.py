"""AIM (AI Platform Initiative) - Closed-Loop Reinforcement Learning & Live Sensing Test Suite (Phase 4)
Verifies:
1. Closed-loop reinforcement learner updating copy pattern weights from POS revenue & CTR
2. Top performing copy patterns autonomous selection
3. Dynamic strategy suggestion based on adaptive owner constraints & conversion weights
4. Open-Meteo coordinate resolution, signal parsing, and provenance ledger verification
"""

import unittest
from datetime import datetime

from aim.core.feedback_learner import FeedbackLearner
from aim.open_meteo_collector import OpenMeteoCollector
from aim.schema import CollectionStatus, EvidenceTier


class TestClosedLoopAndLiveSensing(unittest.TestCase):
    def setUp(self):
        FeedbackLearner.reset_pattern_metrics()

    def test_closed_loop_reinforcement_learning(self):
        # 1. Baseline top pattern check
        top_patterns = FeedbackLearner.get_top_performing_patterns(limit=3)
        self.assertEqual(len(top_patterns), 3)
        self.assertEqual(top_patterns[0]["pattern_theme"], "BENEFIT_CURIOSITY")

        # 2. Record new POS attribution for URGENCY_SCARCITY with high revenue
        updated = FeedbackLearner.record_campaign_attribution(
            campaign_id="CAMP_TEST_01",
            pattern_theme="URGENCY_SCARCITY",
            impressions=500,
            clicks=150,
            conversions=80,
            revenue_krw=3500000,
        )
        self.assertGreater(updated["total_revenue_krw"], 3500000)
        self.assertGreater(updated["weight_score"], 3.0)

        # 3. Verify rank change: URGENCY_SCARCITY should now be top or higher weighted
        new_top = FeedbackLearner.get_top_performing_patterns(limit=1)[0]
        self.assertEqual(new_top["pattern_theme"], "URGENCY_SCARCITY")

    def test_suggest_optimal_strategy_with_adaptive_constraints(self):
        tenant_id = "TENANT_TEST_001"
        FeedbackLearner.clear_tenant_constraints(tenant_id)

        # Record owner negative feedback
        FeedbackLearner.record_feedback(
            tenant_id=tenant_id,
            reason_code="DISCOUNT_TOO_HIGH",
            note="할인율이 너무 커서 마진이 줄어듭니다.",
        )

        suggestion = FeedbackLearner.suggest_optimal_strategy(
            tenant_id=tenant_id,
            situation="우천 시 저녁 타임 손님 유치",
        )
        self.assertTrue(bool(suggestion["recommended_theme"]))
        self.assertGreater(suggestion["theme_weight"], 1.0)
        self.assertEqual(len(suggestion["adaptive_constraints_applied"]), 1)
        self.assertIn("최대 할인율 10%", suggestion["adaptive_constraints_applied"][0])

    def test_open_meteo_coordinate_and_provenance(self):
        # 1. Resolve known coordinates
        coords_seongsu = OpenMeteoCollector.resolve_coordinates("서울 성수동")
        self.assertIsNotNone(coords_seongsu)
        self.assertAlmostEqual(coords_seongsu[0], 37.5445, places=3)
        self.assertAlmostEqual(coords_seongsu[1], 127.0557, places=3)

        coords_gangnam = OpenMeteoCollector.resolve_coordinates("서울 강남")
        self.assertIsNotNone(coords_gangnam)

        # Unknown location returns None (grounding: Karpathy principle)
        coords_unknown = OpenMeteoCollector.resolve_coordinates("미지의가상행성상권")
        self.assertIsNone(coords_unknown)

        # 2. Build URL assertion
        free_url = OpenMeteoCollector.build_url(37.5, 127.0)
        self.assertIn("api.open-meteo.com", free_url)
        self.assertIn("latitude=37.5", free_url)

        # 3. Mock payload signal parsing
        now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
        mock_payload = {
            "hourly": {
                "time": [now_str],
                "temperature_2m": [18.5],
                "precipitation_probability": [80],
                "precipitation": [3.2],
                "weather_code": [61],
            }
        }
        mock_prov = OpenMeteoCollector._failed(
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            url="https://api.open-meteo.com/v1/forecast",
            reason="test",
        )
        mock_prov.status = CollectionStatus.SUCCESS
        mock_prov.evidence_tier = EvidenceTier.A_MEASURED

        signal = OpenMeteoCollector.parse_signal(mock_payload, mock_prov)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.temp_c, 18.5)
        self.assertEqual(signal.precip_prob, 0.8)
        self.assertEqual(signal.precip_mm, 3.2)
        self.assertEqual(signal.weather_code, "61")


if __name__ == "__main__":
    unittest.main()

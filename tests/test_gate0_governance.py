"""AIM Gate 0 Verification Tests (docs/12_multidimensional_data_collection_expert_panel.md)
Validates the Data Governance layer mandated by the expert panel:
1. Every collection path writes a CollectionProvenance ledger.
2. Mock/illustrative data never leaks onto the operational path.
3. Evidence tiers are enforced on financial figures.

Adheres to Karpathy Principle 3: Verify Obsessively.
"""

import unittest

from aim.schema import (
    CollectionProvenance,
    CollectionStatus,
    EvidenceTier,
    PosSummary,
    RawStoreData,
    RawReview,
    StoreInfo,
)
from aim.url_ingester import StoreUrlIngester
from aim.pipeline import AIMPipeline
from aim.normalizer import StoreDataNormalizer


PROBE_URL = "https://collection-failure-probe.invalid/store/1"


class TestGate0EvidenceTier(unittest.TestCase):
    def test_pos_summary_defaults_to_illustrative(self):
        """POS 연동 전까지 POS 요약은 반드시 시연값 등급이어야 한다."""
        pos = PosSummary(analysis_period="2026-10-07", peak_hours="12:00-14:00")
        self.assertEqual(pos.evidence_tier, EvidenceTier.C_ILLUSTRATIVE)

    def test_measured_pos_requires_explicit_tier(self):
        pos = PosSummary(
            analysis_period="2026-10-07",
            peak_hours="12:00-14:00",
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        self.assertEqual(pos.evidence_tier, EvidenceTier.A_MEASURED)

    def test_url_ingester_marks_pos_as_illustrative(self):
        """실제 수집된 URL이라도 POS 값은 실측이 아니므로 C 등급이어야 한다."""
        parsed = StoreUrlIngester.parse_html_content(
            '<html><head><title>테스트 매장</title>'
            '<meta property="og:description" content="테스트 매장 소개 문구입니다." />'
            "</head><body></body></html>",
            "https://m.place.naver.com/restaurant/1",
        )
        raw = StoreUrlIngester.build_initial_raw_data(parsed)
        self.assertEqual(raw.pos_summary.evidence_tier, EvidenceTier.C_ILLUSTRATIVE)


class TestGate0ProvenanceLedger(unittest.TestCase):
    def test_failed_collection_returns_failed_ledger(self):
        """수집 실패 시 raw_data 없이 FAILED 장부를 남겨야 한다."""
        raw, meta, is_live, prov = StoreUrlIngester.ingest_url(PROBE_URL)
        self.assertIsNone(raw)
        self.assertEqual({}, meta)
        self.assertFalse(is_live)
        self.assertIsInstance(prov, CollectionProvenance)
        self.assertEqual(prov.status, CollectionStatus.FAILED)
        self.assertIsNotNone(prov.failure_reason)
        self.assertEqual(prov.record_count, 0)
        self.assertEqual(prov.source_kind, "NAVER_PLACE_URL")

    def test_failed_collection_never_fabricates_figures(self):
        """실패 시 어떤 수치 데이터도 만들어내지 않아야 한다."""
        raw, _, _, _ = StoreUrlIngester.ingest_url(PROBE_URL)
        self.assertIsNone(raw)

    def test_ledger_serializes_for_audit(self):
        prov = CollectionProvenance(
            source_kind="KMA_WEATHER",
            request_target="https://example.com",
            fetched_at="2026-10-07 09:00:00",
            status=CollectionStatus.SUCCESS,
            record_count=1,
            pii_mask_applied=False,
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        dumped = prov.model_dump(mode="json")
        self.assertEqual(dumped["status"], "SUCCESS")
        self.assertEqual(dumped["evidence_tier"], "A_MEASURED")
        self.assertEqual(dumped["source_kind"], "KMA_WEATHER")

    def test_successful_ingestion_carries_ledger(self):
        """성공 경로(모의 파싱 직접 호출)도 장부가 RawStoreData에 부착되어야 한다."""
        parsed = StoreUrlIngester.parse_html_content(
            '<html><head><title>성수 테스트 베이커리</title></head><body></body></html>',
            "https://m.place.naver.com/restaurant/2",
        )
        raw = StoreUrlIngester.build_initial_raw_data(parsed)
        prov = CollectionProvenance(
            source_kind="NAVER_PLACE_URL",
            request_target="https://m.place.naver.com/restaurant/2",
            fetched_at="2026-10-07 09:00:00",
            status=CollectionStatus.SUCCESS,
            record_count=1,
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        raw.collection = prov
        self.assertIsNotNone(raw.collection)
        self.assertEqual(raw.collection.status, CollectionStatus.SUCCESS)


class TestGate0IllustrativeExposure(unittest.TestCase):
    """Gate 0 성공기준 ②: 시연값(C_ILLUSTRATIVE)이 근거등급 없이 노출되는 경로 0건."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from aim.web_app import app
        self.client = TestClient(app)

    def test_intelligence_payloads_declare_evidence_tier(self):
        payload = self.client.get("/api/intelligence").json()
        for c in payload["competitors"]:
            self.assertEqual(c["evidence_tier"], "C_ILLUSTRATIVE")
        self.assertEqual(payload["flash_booster"]["evidence_tier"], "C_ILLUSTRATIVE")
        self.assertEqual(payload["ranking_diagnosis"]["evidence_tier"], "C_ILLUSTRATIVE")
        self.assertIn("실측", payload["flash_booster"]["revenue_basis"])

    def test_approve_response_declares_evidence_tier(self):
        payload = self.client.post(
            "/api/approve", json={"store_id": "S1", "selected_channels": ["naver_blog"]}
        ).json()
        self.assertEqual(payload["evidence_tier"], "C_ILLUSTRATIVE")
        self.assertNotIn("420,000", payload["scheduled_time"])

    def test_tenant_execution_declares_projection_basis(self):
        payload = self.client.post("/api/tenant/execute", json={"tenant_id": "TENANT_001"}).json()
        self.assertEqual(payload["evidence_tier"], "C_ILLUSTRATIVE")
        self.assertIn("실측 POS", payload["projection_basis"])

    def test_admin_panel_declares_illustrative_banner(self):
        html = self.client.get("/").text
        self.assertIn("C_ILLUSTRATIVE", html)
        self.assertIn("시연값", html)


class TestGate0PipelineIntegrity(unittest.TestCase):
    def test_pipeline_backfill_keeps_pos_tier(self):
        """정규화 파이프라인을 통과해도 POS 등급 정보가 유실되지 않아야 한다."""
        raw = RawStoreData(
            store_info=StoreInfo(
                store_id="S1",
                name="테스트",
                category="베이커리/디저트",
                address="서울",
                business_hours="09:00-21:00",
            ),
            pos_summary=PosSummary(
                analysis_period="2026-10-07",
                peak_hours="12:00-14:00",
                top_selling_items=[],
            ),
            raw_reviews=[RawReview(review_id="R1", source="x", author="a", rating=5.0, text="테스트 리뷰")],
        )
        self.assertEqual(raw.pos_summary.evidence_tier, EvidenceTier.C_ILLUSTRATIVE)
        profile = StoreDataNormalizer.normalize(raw)
        self.assertEqual(profile.store_name, "테스트")

    def test_end_to_end_pipeline_unaffected(self):
        """기존 엔드투엔드 파이프라인이 회귀 없이 동작하는지 확인 (docs/12 G0 회귀 0 기준)."""
        package = AIMPipeline("data/sample_store.json").run()
        self.assertIn("naver_blog", package.channels)
        self.assertIn("instagram", package.channels)
        self.assertIn("kakaotalk", package.channels)


if __name__ == "__main__":
    unittest.main()
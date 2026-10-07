"""Tests for P0-2 POS 정산 파일 수집기 (docs/12 P0-2)
Validates:
1. 정산 CSV → SalesLedgerFact 1건 (A_MEASURED) 생성
2. 시간대별 유휴율 계산이 정원(분모) 없이는 절대 산출되지 않음
3. 실패 시 모의값으로 대체하지 않고 FAILED 장부를 남김
4. 실측 사실이 BusinessState를 교체하며 원본 상태를 변형하지 않음
5. 테넌트 포털 업로드 API 계약
"""

import os
import unittest

from fastapi.testclient import TestClient

from aim.schema import BusinessState, CollectionStatus, EvidenceTier, SalesLedgerFact
from aim.pos_ledger_ingester import SalesLedgerIngester
from aim.web_app import app

SAMPLE_LEDGER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "sample_pos_ledger.csv"
)


def _sample_text() -> str:
    with open(SAMPLE_LEDGER, "r", encoding="utf-8") as f:
        return f.read()


class TestPosLedgerParsing(unittest.TestCase):
    def test_sample_csv_yields_one_measured_fact(self):
        """정산 CSV 1건 → SalesLedgerFact 1건, 근거 등급 A_MEASURED."""
        fact, provenance = SalesLedgerIngester.ingest_csv(
            _sample_text(), source_label="sample_pos_ledger.csv"
        )

        self.assertIsNotNone(fact)
        self.assertEqual(provenance.status, CollectionStatus.SUCCESS)
        self.assertEqual(provenance.evidence_tier, EvidenceTier.A_MEASURED)
        self.assertEqual(fact.evidence_tier, EvidenceTier.A_MEASURED)

        # 손계산 대조: 결제 124건 / 2,976,000원 / 객단가 24,000원
        self.assertEqual(fact.business_date, "2026-10-06")
        self.assertEqual(fact.transaction_count, 124)
        self.assertEqual(fact.gross_revenue_krw, 2976000)
        self.assertEqual(fact.avg_ticket_krw, 24000)
        self.assertEqual(provenance.record_count, 14)

    def test_idle_rate_computed_per_hour_slot(self):
        """유휴율 = (정원 - 실 결제) / 정원, 시간대별로 계산된다."""
        fact, _ = SalesLedgerIngester.ingest_csv(_sample_text())

        # 15시: 18석 중 3건 사용 → 유휴 83.3%
        self.assertAlmostEqual(fact.slot_idle_rate["15:00"], 0.8333, places=4)
        # 19시: 18석 중 17건 사용 → 유휴 5.6%
        self.assertAlmostEqual(fact.slot_idle_rate["19:00"], 0.0556, places=4)
        self.assertAlmostEqual(fact.idle_capacity_rate, 0.5079, places=4)

    def test_low_stock_items_deduplicated(self):
        fact, _ = SalesLedgerIngester.ingest_csv(_sample_text())
        self.assertEqual(fact.low_stock_items, ["통밀사워도우", "라벤더라떼"])

    def test_multiple_business_dates_use_latest_day_only(self):
        """여러 날이 섞이면 평균을 섞지 않고 최근 영업일 하나만 대표로 삼는다."""
        csv_text = (
            "영업일,시간대,결제건수,매출액,테이블수\n"
            "2026-10-05,14:00,1,24000,10\n"
            "2026-10-06,14:00,5,120000,10\n"
        )
        fact, _ = SalesLedgerIngester.ingest_csv(csv_text)

        self.assertEqual(fact.business_date, "2026-10-06")
        self.assertEqual(fact.transaction_count, 5)
        self.assertEqual(fact.gross_revenue_krw, 120000)

    def test_idle_rate_clamped_when_oversold(self):
        """정원을 초과한 회계 보정이 들어와도 유휴율이 음수가 되지 않는다."""
        csv_text = (
            "영업일,시간대,결제건수,매출액,테이블수\n2026-10-06,14:00,15,300000,10\n"
        )
        fact, _ = SalesLedgerIngester.ingest_csv(csv_text)
        self.assertEqual(fact.slot_idle_rate["14:00"], 0.0)

    def test_cp949_encoded_payload_supported(self):
        """국내 POS 파일의 cp949 인코딩을 그대로 받아들인다."""
        fact, provenance = SalesLedgerIngester.ingest_csv(
            _sample_text().encode("cp949")
        )
        self.assertIsNotNone(fact)
        self.assertEqual(fact.avg_ticket_krw, 24000)
        self.assertIsNone(provenance.failure_reason)

    def test_vendor_header_aliases_resolved(self):
        """업체마다 다른 헤더 표기를 별칭 사전으로 흡수한다."""
        csv_text = (
            "일자,시각,주문건수,결제합계,정원\n"
            "20261006,14시,4,\"96,000원\",18\n"
        )
        fact, _ = SalesLedgerIngester.ingest_csv(csv_text)
        self.assertEqual(fact.business_date, "2026-10-06")
        self.assertEqual(fact.transaction_count, 4)
        self.assertEqual(fact.gross_revenue_krw, 96000)
        self.assertAlmostEqual(fact.slot_idle_rate["14:00"], 1 - 4 / 18, places=4)


class TestPosLedgerHonesty(unittest.TestCase):
    """Gate 0 취지: 못 읽으면 실패로 보고하고 절대 추정치로 메우지 않는다."""

    def test_missing_capacity_column_is_a_failure_not_an_estimate(self):
        csv_text = "영업일,시간대,결제건수,매출액\n2026-10-06,14:00,4,96000\n"
        fact, provenance = SalesLedgerIngester.ingest_csv(csv_text)

        self.assertIsNone(fact)
        self.assertEqual(provenance.status, CollectionStatus.FAILED)
        self.assertEqual(provenance.evidence_tier, EvidenceTier.C_ILLUSTRATIVE)
        self.assertIn("capacity_units", provenance.failure_reason)

    def test_zero_capacity_row_never_produces_a_percentage(self):
        """정원 0은 '0% 가득 찼다'가 아니라 '계산 불가'다."""
        csv_text = (
            "영업일,시간대,결제건수,매출액,테이블수\n2026-10-06,14:00,0,0,0\n"
        )
        fact, provenance = SalesLedgerIngester.ingest_csv(csv_text)

        self.assertIsNone(fact)
        self.assertEqual(provenance.status, CollectionStatus.FAILED)
        self.assertIn("유휴율 산출 불가", provenance.failure_reason)

    def test_empty_payload_fails(self):
        fact, provenance = SalesLedgerIngester.ingest_csv("   ")
        self.assertIsNone(fact)
        self.assertEqual(provenance.status, CollectionStatus.FAILED)
        self.assertIn("비어 있습니다", provenance.failure_reason)

    def test_header_only_file_fails(self):
        fact, provenance = SalesLedgerIngester.ingest_csv(
            "영업일,시간대,결제건수,매출액,테이블수\n"
        )
        self.assertIsNone(fact)
        self.assertEqual(provenance.status, CollectionStatus.FAILED)

    def test_binary_payload_fails_instead_of_decoding_as_mojibake(self):
        """깨진 바이너리는 latin-1로 통과시키지 않고 실패로 보고한다."""
        fact, provenance = SalesLedgerIngester.ingest_csv(
            b"\xff\xfe\x00\x01\x80\x81\x82"
        )
        self.assertIsNone(fact)
        self.assertEqual(provenance.status, CollectionStatus.FAILED)
        self.assertIn("인코딩", provenance.failure_reason)

    def test_unparsable_number_reports_the_offending_row(self):
        csv_text = (
            "영업일,시간대,결제건수,매출액,테이블수\n2026-10-06,14:00,사십,96000,18\n"
        )
        fact, provenance = SalesLedgerIngester.ingest_csv(csv_text)

        self.assertIsNone(fact)
        self.assertIn("2행", provenance.failure_reason)

    def test_partial_bad_rows_are_recorded_but_do_not_discard_the_day(self):
        """정상 행이 하나라도 있으면 측정치를 내고, 누락 건수를 장부에 남긴다."""
        csv_text = (
            "영업일,시간대,결제건수,매출액,테이블수\n"
            "2026-10-06,14:00,4,96000,18\n"
            "2026-10-06,15:00,사십,96000,18\n"
        )
        fact, provenance = SalesLedgerIngester.ingest_csv(csv_text)

        self.assertIsNotNone(fact)
        self.assertEqual(fact.transaction_count, 4)
        self.assertEqual(provenance.status, CollectionStatus.SUCCESS)
        self.assertIn("3행", provenance.failure_reason)


class TestMeasuredStateBridge(unittest.TestCase):
    def _state(self) -> BusinessState:
        return BusinessState(
            domain="fnb",
            entity_name="테스트 매장",
            location="서울 성수동",
            target_audience="2030 MZ",
            core_usps=["테스트 USP"],
            idle_capacity_rate=0.35,
            trigger_event="기존 시연값 트리거",
            unit_price=24000,
        )

    def test_measured_fact_overrides_idle_rate_and_ticket(self):
        fact, _ = SalesLedgerIngester.ingest_csv(_sample_text())
        measured = SalesLedgerIngester.apply_to_business_state(fact, self._state())

        self.assertEqual(measured.idle_capacity_rate, fact.idle_capacity_rate)
        self.assertEqual(measured.unit_price, 24000)
        self.assertIn("정산 실측", measured.trigger_event)

    def test_original_business_state_is_not_mutated(self):
        """승격은 새 객체를 만들어야 한다. 원본이 바뀌면 조용한 데이터 오염이 된다."""
        original = self._state()
        fact, _ = SalesLedgerIngester.ingest_csv(_sample_text())
        SalesLedgerIngester.apply_to_business_state(fact, original)

        self.assertEqual(original.idle_capacity_rate, 0.35)
        self.assertEqual(original.trigger_event, "기존 시연값 트리거")

    def test_non_measured_fact_is_refused(self):
        illustrative = SalesLedgerFact(
            source="POS_FILE",
            captured_at="2026-10-07 10:00:00",
            business_date="2026-10-06",
            transaction_count=10,
            gross_revenue_krw=240000,
            avg_ticket_krw=24000,
            slot_idle_rate={"14:00": 0.5},
            evidence_tier=EvidenceTier.C_ILLUSTRATIVE,
        )
        with self.assertRaises(ValueError):
            SalesLedgerIngester.apply_to_business_state(illustrative, self._state())


class TestPosLedgerApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_upload_grades_to_measured_and_shows_impact(self):
        res = self.client.post(
            "/api/v1/tenant/TENANT_001/pos-ledger",
            json={"csv_text": _sample_text(), "source_label": "sample_pos_ledger.csv"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["evidence_tier"], "A_MEASURED")
        self.assertEqual(data["collection"]["status"], "SUCCESS")
        self.assertAlmostEqual(data["idle_capacity_rate"], 0.5079, places=4)

        preview = data["impact_preview"]
        self.assertNotEqual(
            preview["before_illustrative"]["idle_capacity_rate"],
            preview["after_measured"]["idle_capacity_rate"],
        )

    def test_unreadable_file_returns_422_with_failed_ledger(self):
        res = self.client.post(
            "/api/v1/tenant/TENANT_001/pos-ledger",
            json={"csv_text": "영업일,시간대,결제건수,매출액\n2026-10-06,14:00,4,96000\n"},
        )
        self.assertEqual(res.status_code, 422)
        detail = res.json()["detail"]
        self.assertEqual(detail["status"], "COLLECTION_FAILED")
        self.assertEqual(detail["collection"]["status"], "FAILED")
        self.assertEqual(detail["collection"]["evidence_tier"], "C_ILLUSTRATIVE")

    def test_upload_does_not_execute_or_bill_the_tenant(self):
        """정산 업로드는 측정만 한다. 발송·과금은 원클릭 승인 경로의 몫이다."""
        before = self.client.get("/api/v1/tenant/TENANT_001").json()["tenant"]

        self.client.post(
            "/api/v1/tenant/TENANT_001/pos-ledger", json={"csv_text": _sample_text()}
        )

        after = self.client.get("/api/v1/tenant/TENANT_001").json()["tenant"]
        self.assertEqual(before["total_campaigns_executed"], after["total_campaigns_executed"])
        self.assertEqual(
            before["cumulative_revenue_generated_krw"], after["cumulative_revenue_generated_krw"]
        )
        self.assertEqual(before["business_state"]["idle_capacity_rate"], 0.35)

    def test_unknown_tenant_returns_404(self):
        res = self.client.post(
            "/api/v1/tenant/TENANT_999/pos-ledger", json={"csv_text": _sample_text()}
        )
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
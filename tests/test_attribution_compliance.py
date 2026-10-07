"""Tests for CC BY 4.0 데이터 출처 표기 강제 (docs/19)

이 스위트가 지킨다:
1. 기상 데이터를 실제로 썼을 때만 출처 표기가 나온다 (노이즈 방지).
2. 표기가 요구될 때 누락은 컴플라이언스 위반으로 판정된다.
3. 표기가 없으면 **발송이 보류된다** (방어가 장식이 되면 안 된다).
4. 표기가 없는 컨텍스트는 판정하지 않는다 (오탐 방지).
5. 출처는 텍스트가 아니라 데이터로 기록된다 (문자열 추측 금지).
"""

import unittest
from datetime import datetime

from aim.core.compliance_engine import ATTRIBUTION_RULE_CATEGORY, ComplianceEngine
from aim.core.context_engine import ContextEngine
from aim.core.platform import AIMPlatform
from aim.environment_sensor import EnvironmentSensor
from aim.open_meteo_collector import ATTRIBUTION_TEXT
from aim.schema import EvidenceTier
from aim.tenant.manager import TenantManager


def weather_signal(**fields):
    """기상 필드가 채워진 신호 (테스트 픽스처)."""
    base = EnvironmentSensor.resolve_holiday_signal(datetime(2026, 10, 7, 15))
    updates = {
        "weather_code": "63",
        "weather_code_system": "WMO",
        "precip_prob": 0.8,
        "precip_mm": 4.2,
        "temp_c": 16.0,
        "evidence_tier": EvidenceTier.A_MEASURED,
    }
    updates.update(fields)
    return base.model_copy(update=updates)


def tenant_state():
    return TenantManager.get_tenant("TENANT_001").business_state


class TestAttributionOnlyWhenWeatherIsUsed(unittest.TestCase):
    def test_measured_weather_produces_attribution(self):
        plan = AIMPlatform.plan_campaign(tenant_state(), env_signal=weather_signal())

        self.assertEqual(plan.attribution, ATTRIBUTION_TEXT)
        for payload in plan.channels.values():
            self.assertEqual(payload.attribution, ATTRIBUTION_TEXT)
            self.assertIn(ATTRIBUTION_TEXT, payload.body)

    def test_no_weather_means_no_attribution(self):
        """항상 붙이면 표기가 노이즈가 되어 진짜 의무를 흐린다."""
        plan = AIMPlatform.plan_campaign(tenant_state())

        self.assertIsNone(plan.attribution)
        for payload in plan.channels.values():
            self.assertIsNone(payload.attribution)
            self.assertNotIn("Open-Meteo", payload.body)

    def test_attribution_appears_in_every_channel(self):
        """한 채널만 빠지면 그 채널에서 라이선스 위반이 된다."""
        plan = AIMPlatform.plan_campaign(tenant_state(), env_signal=weather_signal())
        self.assertEqual(len(plan.channels), 3)
        for key, payload in plan.channels.items():
            self.assertIn(ATTRIBUTION_TEXT, payload.body, key)


class TestProvenanceIsDataNotText(unittest.TestCase):
    def test_provenance_records_the_actual_source(self):
        """출처를 문자열에서 찾지 않고 데이터로 기록한다."""
        signal = weather_signal()
        signal.collection = signal.collection.model_copy(
            update={"source_kind": "OPEN_METEO"}
        )
        ctx = ContextEngine.build_context(
            domain="fnb", location="서울 성수동", target_audience="2030 MZ",
            situation="테스트", env_signal=signal,
        )

        self.assertIn("OPEN_METEO", ctx.provenance.sources)
        self.assertTrue(ctx.provenance.weather_collected)
        self.assertEqual(ctx.provenance.required_attribution, ATTRIBUTION_TEXT)

    def test_astronomy_only_provenance_requires_nothing(self):
        ctx = ContextEngine.build_context(
            domain="fnb", location="서울 성수동", target_audience="2030 MZ",
            situation="테스트",
        )
        self.assertFalse(ctx.provenance.weather_collected)
        self.assertIsNone(ctx.provenance.required_attribution)

    def test_astronomy_derived_context_is_default(self):
        """기존 호출부가 명시하지 않으면 천문 파생으로 간주된다."""
        ctx = ContextEngine.build_context(
            domain="fnb", location="서울 성수동", target_audience="2030 MZ"
        )
        self.assertIn("ASTRONOMY_CALENDAR", ctx.provenance.sources)


class TestComplianceAudit(unittest.TestCase):
    def test_missing_attribution_is_a_violation(self):
        report = ComplianceEngine.audit(
            "비 오는 날 안내입니다.", "fnb", required_attribution=ATTRIBUTION_TEXT
        )
        self.assertFalse(report.is_compliant)
        categories = [v.rule_category for v in report.violations]
        self.assertIn(ATTRIBUTION_RULE_CATEGORY, categories)

    def test_present_attribution_passes(self):
        report = ComplianceEngine.audit(
            f"안내입니다.\n\n*{ATTRIBUTION_TEXT}*",
            "fnb", required_attribution=ATTRIBUTION_TEXT,
        )
        self.assertTrue(report.is_compliant)

    def test_no_requirement_means_no_check(self):
        """기상 미사용 카피에 출처를 요구하면 안 된다 (오탐)."""
        report = ComplianceEngine.audit("최고의 빵입니다", "fnb")
        self.assertFalse(report.is_compliant)  # 광고법 위반은 잡힘
        self.assertNotIn(
            ATTRIBUTION_RULE_CATEGORY, [v.rule_category for v in report.violations]
        )

    def test_engine_generated_copy_is_never_in_violation(self):
        """합성 엔진이 붙이므로 자기 산출물은 스스로 위반하지 않는다."""
        plan = AIMPlatform.plan_campaign(tenant_state(), env_signal=weather_signal())
        for key, payload in plan.channels.items():
            self.assertTrue(payload.compliance_report.is_compliant, key)


class TestDispatchIsBlocked(unittest.TestCase):
    def _plan_missing_attribution(self):
        """합성을 우회한 외부 입력 흉내: 출처 표기가 빠진 채널."""
        plan = AIMPlatform.plan_campaign(tenant_state())
        plan.channels["direct"].compliance_report = ComplianceEngine.audit(
            "비 오는 날 special_offer", "fnb", required_attribution=ATTRIBUTION_TEXT
        )
        return plan

    def test_missing_attribution_blocks_dispatch(self):
        """방어가 장식이 되면 안 된다. 표기가 없으면 나가면 안 된다."""
        result = AIMPlatform.execute_campaign(self._plan_missing_attribution())

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["dispatched_channels"], [])
        self.assertIn("direct", result["blocked_channels"])

    def test_blocked_dispatch_reports_zero_projected_revenue(self):
        """보류된 발송이 매출로 집계되면 안 된다."""
        result = AIMPlatform.execute_campaign(self._plan_missing_attribution())
        self.assertEqual(result["projected_revenue"], 0)

    def test_dispatch_resumes_once_attribution_is_added(self):
        plan = self._plan_missing_attribution()
        plan.channels["direct"].compliance_report = ComplianceEngine.audit(
            f"비 오는 날 special_offer\n\n*{ATTRIBUTION_TEXT}*",
            "fnb", required_attribution=ATTRIBUTION_TEXT,
        )
        result = AIMPlatform.execute_campaign(plan)

        self.assertEqual(result["status"], "DISPATCHED")
        self.assertIn("direct", result["dispatched_channels"])

    def test_normal_plan_dispatches(self):
        """회귀 방지: 정상 계획은 그대로 발송된다."""
        result = AIMPlatform.execute_campaign(AIMPlatform.plan_campaign(tenant_state()))
        self.assertEqual(result["status"], "DISPATCHED")
        self.assertEqual(len(result["dispatched_channels"]), 3)

    def test_sanitized_ad_copy_is_still_dispatchable(self):
        """표시광고법 위반은 본문이 교정본이므로 막지 않는다 (기존 동작 유지)."""
        plan = AIMPlatform.plan_campaign(tenant_state())
        plan.channels["blog"].compliance_report = ComplianceEngine.audit(
            "국내 최고 빵입니다", "fnb"
        )
        self.assertFalse(plan.channels["blog"].compliance_report.is_compliant)

        result = AIMPlatform.execute_campaign(plan)
        self.assertEqual(result["status"], "DISPATCHED")


class TestLicenceTermsAreHonest(unittest.TestCase):
    def test_attribution_names_the_source_and_the_licence(self):
        self.assertIn("Open-Meteo", ATTRIBUTION_TEXT)
        self.assertIn("CC BY 4.0", ATTRIBUTION_TEXT)

    def test_commercial_endpoint_still_requires_a_key(self):
        """표기를 붙이는 것과 상업 라이선스를 얻는 것은 별개다."""
        from aim.open_meteo_collector import (
            COMMERCIAL_ENDPOINT,
            CommercialLicenceRequired,
            assert_commercial_use,
        )

        with self.assertRaises(CommercialLicenceRequired):
            assert_commercial_use(None, COMMERCIAL_ENDPOINT)


if __name__ == "__main__":
    unittest.main()
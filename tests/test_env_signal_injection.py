"""Tests for P0-3 EnvironmentSignal 오버라이드 주입 (docs/13 P0-3, docs/16)

Validates the contract that makes a future KMA collector meaningful:
1. 주입된 실측 신호가 실제로 `situation`에 반영된다 (이게 P0-3의 본질).
2. 실측 기상이 F&B 날씨 트리거를 실제로 발동시킨다.
3. 강수확률 문턱 미달은 가짜 경보가 되지 않는다.
4. 키가 없는 기존 경로 출력은 P0-3 이전과 완전히 동일하다 (무파괴 증명).
5. 계절·요일이 주입된 신호의 날짜에서 계산된다.
6. 매핑되지 않은 기상 코드는 지어내지 않는다.

docs/13이 지시한 제약: "기존 코드 파괴 없이". 4번이 그 제약의 직접 증거다.
"""

import unittest
from datetime import datetime

from aim.core.context_engine import ContextEngine
from aim.core.platform import AIMPlatform
from aim.domains.fnb import FnbDomainPlugin
from aim.environment_sensor import (
    KMA_SKY_WEATHER_CODES,
    RAIN_TRIGGER_THRESHOLD,
    EnvironmentSensor,
)
from aim.schema import BusinessState, EnvironmentSignal, EvidenceTier
from aim.tenant.manager import TenantManager


def _base_signal() -> EnvironmentSignal:
    """키 없이 계산되는 기준 신호 (P0-1 경로)."""
    return EnvironmentSensor.resolve_holiday_signal(datetime(2026, 10, 7, 15))


def _with_weather(signal: EnvironmentSignal, **fields) -> EnvironmentSignal:
    """수집기가 기상 필드를 채웠음을 흉내내는 테스트 픽스처.

    테스트 안에서만 쓰는 명시적 픽스처이며, 운영 코드에는 기상 값을 만들어
    내는 경로가 존재하지 않는다. 운영 수집기는 P1-0에서 구현된다.
    """
    updates = {"evidence_tier": EvidenceTier.A_MEASURED}
    updates.update(fields)
    return signal.model_copy(update=updates)


class TestWeatherClause(unittest.TestCase):
    def test_weather_fields_now_reach_the_situation_string(self):
        """P0-3의 핵심 계약: 실측 기상이 situation에 나타난다.

        P0-3 이전에는 temp_c/precip_prob/weather_code를 읽는 코드가 어디에도
        없었으므로, 이 결과는 빈 문자열 추가로 끝났을 것이다.
        """
        signal = _with_weather(
            _base_signal(),
            weather_code="4",
            weather_code_system="KMA_SKY",
            precip_prob=0.8,
            temp_c=18.0,
        )
        text = EnvironmentSensor.describe_situation(signal)

        self.assertIn("강수확률 80%", text)
        self.assertIn("18도", text)
        self.assertIn("약한 비", text)

    def test_ambiguous_code_without_a_system_is_not_guessed(self):
        """체계를 밝히지 않은 코드는 추측하지 않는다 (docs/17 §2).

        KMA SKY 4와 WMO 체계는 숫자 4의 뜻이 다르다. 어느 쪽인지 모르면 라벨을
        지어내지 않고 강수확률처럼 독립적인 수치만 보여준다.
        """
        signal = _with_weather(_base_signal(), weather_code="4", precip_prob=0.8, temp_c=18.0)
        text = EnvironmentSensor.describe_situation(signal)

        self.assertNotIn("약한 비", text)
        self.assertIn("비 예보", text)  # 문턱 초과로만 표시되는 폴백 라벨
        self.assertIn("강수확률 80%", text)

    def test_rain_probability_is_reported_regardless_of_threshold(self):
        """문턱 미달이어도 측정값 자체는 숨기지 않는다."""
        signal = _with_weather(_base_signal(), precip_prob=0.1, temp_c=21.0)
        text = EnvironmentSensor.describe_weather(signal)

        self.assertIn("강수확률 10%", text)
        self.assertNotIn("비 예보", text)

    def test_no_code_but_high_probability_states_rain_forecast(self):
        """초단기처럼 SKY 코드가 없고 강수확률만 주는 응답도 처리된다."""
        signal = _with_weather(_base_signal(), precip_prob=0.85, temp_c=16.0)
        text = EnvironmentSensor.describe_weather(signal)

        self.assertIn("비 예보", text)
        self.assertIn("강수확률 85%", text)

    def test_unmapped_weather_code_is_not_guessed(self):
        """표에 없는 코드는 라벨을 지어내지 않고 수치만 보여준다."""
        signal = _with_weather(_base_signal(), weather_code="99", temp_c=20.0)
        text = EnvironmentSensor.describe_weather(signal)

        self.assertEqual(text, "20도")

    def test_no_weather_means_no_clause_at_all(self):
        """미수집이면 조용히 사라진다 (기존 동작 보존)."""
        self.assertIsNone(EnvironmentSensor.describe_weather(_base_signal()))

    def test_threshold_boundary_is_inclusive(self):
        signal = _with_weather(_base_signal(), precip_prob=RAIN_TRIGGER_THRESHOLD)
        self.assertIn("비 예보", EnvironmentSensor.describe_weather(signal))

        below = _with_weather(_base_signal(), precip_prob=RAIN_TRIGGER_THRESHOLD - 0.01)
        self.assertNotIn("비 예보", EnvironmentSensor.describe_weather(below))

    def test_every_documented_code_has_a_label(self):
        """매핑표에 빈 라벨이 있으면 안 된다 (키가 왔을 때 빈 문자열로 새지 않음)."""
        for code, label in KMA_SKY_WEATHER_CODES.items():
            self.assertTrue(label.strip(), f"code {code} has an empty label")


class TestMeasuredWeatherReachesDomainPlugins(unittest.TestCase):
    """측정값이 도메인 플러그인의 트리거를 실제로 발동시키는가."""

    def _fnc_state(self) -> BusinessState:
        """유휴는 없는 상태. 오직 날씨 트리거만으로 판정되도록 한다."""
        return BusinessState(
            domain="fnb",
            entity_name="테스트 카페",
            location="서울 성동구 성수동",
            target_audience="2030 MZ세대",
            core_usps=["테스트 USP"],
            idle_capacity_rate=0.0,
            trigger_event="정기 점검 중",
            unit_price=24000,
        )

    def test_measured_rain_fires_the_fnb_weather_trigger(self):
        state = self._fnc_state()
        rainy = _with_weather(
            _base_signal(),
            weather_code="4",
            weather_code_system="KMA_SKY",
            precip_prob=0.8,
            temp_c=16.0,
        )

        plan = AIMPlatform.plan_campaign(state, env_signal=rainy)

        self.assertIn("비", plan.context_vector.situation)
        self.assertEqual(plan.strategy.objective_type, "CAPACITY_RESCUE")
        self.assertEqual(
            plan.strategy.objective_type,
            FnbDomainPlugin().evaluate_triggers(
                state, plan.context_vector
            ).objective_type,
        )

    def test_dry_day_does_not_fire_the_weather_trigger(self):
        """유휴 0% + 맑은 날 → 날씨 트리거가 발동하지 않아야 한다."""
        state = self._fnc_state()
        clear = _with_weather(_base_signal(), weather_code="0", precip_prob=0.0, temp_c=24.0)

        plan = AIMPlatform.plan_campaign(state, env_signal=clear)

        self.assertNotIn("비 예보", plan.context_vector.situation)
        self.assertEqual(plan.strategy.objective_type, "OPPORTUNITY_CAPTURE")


class TestInjectionIsNonDestructive(unittest.TestCase):
    """문서 13의 제약 "기존 코드 파괴 없이"를 검증한다."""

    def test_key_free_path_is_byte_identical_to_before_p0_3(self):
        """P0-3 이전 동작: 날짜·주간길이·절기·일몰·현재시각 만 담는다."""
        signal = _base_signal()
        text = EnvironmentSensor.describe_situation(signal)

        self.assertEqual(
            text, "수 · 11시간 35분 · 추분 · 일몰 18:19 · 15시"
        )

    def test_caller_situation_still_wins_when_nothing_is_injected(self):
        """주입이 없으면 사람이 쓴 situation 문자열이 그대로 쓰인다."""
        ctx = ContextEngine.build_context(
            domain="fnb",
            location="서울 성수동",
            target_audience="2030 MZ",
            situation="테스트베드 시나리오 문자열",
        )
        self.assertEqual(ctx.situation, "테스트베드 시나리오 문자열")

    def test_tenant_plan_campaign_without_injection_is_unchanged(self):
        """기존 호출부(AIMPlatform.plan_campaign(state))가 영향받지 않는다."""
        tenant = TenantManager.get_tenant("TENANT_001")
        plan = AIMPlatform.plan_campaign(tenant.business_state)

        self.assertEqual(
            plan.context_vector.situation, tenant.business_state.trigger_event
        )

    def test_injected_signal_outranks_caller_text(self):
        """핵심 설계 규칙: 명시적 주입은 사람이 쓴 문자열보다 우선한다.

        이 순서가 아니면 수집기를 붙일 때 측정이 trigger_event 문자열에 묻힌다.
        """
        rainy = _with_weather(
            _base_signal(),
            weather_code="4",
            weather_code_system="KMA_SKY",
            precip_prob=0.8,
            temp_c=16.0,
        )
        ctx = ContextEngine.build_context(
            domain="fnb",
            location="서울 성수동",
            target_audience="2030 MZ",
            situation="정기 점검 중",
            env_signal=rainy,
        )

        self.assertIn("정기 점검 중", ctx.situation)
        self.assertIn("강수확률 80%", ctx.situation)


class TestInjectedSignalDateDrivesSeason(unittest.TestCase):
    """주입 신호가 미래 예보일 때 날짜와 계절이 어긋나지 않아야 한다."""

    def _build(self, target: datetime, **weather):
        signal = _with_weather(
            EnvironmentSensor.resolve_holiday_signal(target), **weather
        )
        return ContextEngine.build_context(
            domain="fnb",
            location="서울 성수동",
            target_audience="2030 MZ",
            situation="평소 영업",
            env_signal=signal,
        )

    def test_december_signal_yields_winter_not_autumn(self):
        ctx = self._build(datetime(2026, 12, 22, 9), weather_code="7", precip_prob=0.9, temp_c=-4.0)
        self.assertIn("겨울", ctx.season)
        self.assertIn("화", ctx.situation)  # 2026-12-22는 화요일

    def test_spring_signal_yields_spring(self):
        ctx = self._build(datetime(2026, 2, 10, 9), weather_code="0", temp_c=8.0)
        self.assertIn("봄", ctx.season)

    def test_weekday_comes_from_the_injected_date(self):
        ctx = self._build(datetime(2026, 10, 7, 15))
        self.assertIn("수", ctx.situation)  # 2026-10-07은 수요일

    def test_unparsable_dates_degrade_to_now_instead_of_crashing(self):
        signal = EnvironmentSignal.model_validate(
            {
                "captured_at": "잘못된 시각",
                "observed_date": "잘못된 날짜",
                "day_of_week": 0,
                "day_length": "11시간",
            }
        )
        text = EnvironmentSensor.describe_situation(signal)
        self.assertTrue(text)


if __name__ == "__main__":
    unittest.main()
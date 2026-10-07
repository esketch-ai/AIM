"""Tests for 날씨 기반 소비심리·수요 탄력도 모델 (docs/18)

이 스위트가 지킨다:
1. 출처 없는 규칙은 배포될 수 없다.
2. 문헌 규칙은 이 매장의 규칙이 아니다 (등급 B 유지).
3. 표본이 얕으면 승격하지 않는다.
4. 실측 규칙은 문헌 규칙을 **대체**한다 (합산하지 않는다).
5. 축 상쇄 후 합계는 가장 보수적인 등급을 따른다.
6. 기상 미수집에서는 아무 것도 만들어내지 않는다.
"""

import unittest

from aim.schema import EnvironmentSignal, EvidenceTier, SalesLedgerFact
from aim.weather_psychology import (
    AXIS_BASKET,
    AXIS_FREQUENCY,
    AXIS_VISIT,
    COND_CLEAR,
    COND_HEAT,
    COND_RAIN,
    LITERATURE_RULES,
    DemandCalibrator,
    DemandRule,
    StoreElasticityProfile,
    WeatherDemandModel,
)


def signal(**weather) -> EnvironmentSignal:
    base = {
        "captured_at": "2026-10-07 15:00:00",
        "observed_date": "2026-10-07",
        "day_length": "11시간 35분",
        "solar_term": "추분",
    }
    base.update(weather)
    return EnvironmentSignal.model_validate(base)


def fact(date, txn, ticket, idle) -> SalesLedgerFact:
    return SalesLedgerFact(
        source="POS_FILE",
        captured_at=date,
        business_date=date,
        transaction_count=txn,
        gross_revenue_krw=txn * ticket,
        avg_ticket_krw=ticket,
        slot_idle_rate={"14:00": idle},
        evidence_tier=EvidenceTier.A_MEASURED,
    )


def rainy_day(**over):
    return signal(weather_code="63", weather_code_system="WMO", precip_prob=0.8,
                  precip_mm=4.2, temp_c=16.0, **over)


class TestRulesMustCarryEvidence(unittest.TestCase):
    def test_rule_without_a_source_cannot_be_created(self):
        """근거 없는 규칙이 매출 약속으로 이어지는 길목을 코드에서 막는다."""
        with self.assertRaises(ValueError):
            DemandRule(
                rule_id="NO_SOURCE", condition=COND_RAIN, axis=AXIS_BASKET,
                direction=1, magnitude=0.3, mechanism="ㅅ", source="",
                source_kind="HEURISTIC", evidence_tier=EvidenceTier.C_ILLUSTRATIVE,
            )

    def test_unknown_axis_is_rejected(self):
        with self.assertRaises(ValueError):
            DemandRule(
                rule_id="BAD_AXIS", condition=COND_RAIN, axis="CHARISMA",
                direction=1, magnitude=0.3, mechanism="ㅅ", source="paper",
                source_kind="LITERATURE", evidence_tier=EvidenceTier.B_DERIVED,
            )

    def test_unknown_condition_is_rejected(self):
        with self.assertRaises(ValueError):
            DemandRule(
                rule_id="BAD_COND", condition="HOROSCOPE", axis=AXIS_BASKET,
                direction=1, magnitude=0.3, mechanism="ㅅ", source="paper",
                source_kind="LITERATURE", evidence_tier=EvidenceTier.B_DERIVED,
            )

    def test_absurd_magnitude_is_rejected(self):
        """300% 변화를 '영향 크기'로 쓸 수 있게 두지 않는다."""
        with self.assertRaises(ValueError):
            DemandRule(
                rule_id="TOO_BIG", condition=COND_RAIN, axis=AXIS_BASKET,
                direction=1, magnitude=3.0, mechanism="ㅅ", source="paper",
                source_kind="LITERATURE", evidence_tier=EvidenceTier.B_DERIVED,
            )

    def test_zero_magnitude_is_rejected(self):
        with self.assertRaises(ValueError):
            DemandRule(
                rule_id="ZERO", condition=COND_RAIN, axis=AXIS_BASKET,
                direction=1, magnitude=0.0, mechanism="ㅅ", source="paper",
                source_kind="LITERATURE", evidence_tier=EvidenceTier.B_DERIVED,
            )

    def test_every_shipped_rule_carries_a_source_and_a_scope_note(self):
        for rule in LITERATURE_RULES:
            self.assertTrue(rule.source.strip(), rule.rule_id)
            self.assertTrue(rule.source_kind.strip(), rule.rule_id)
            self.assertEqual(rule.evidence_tier, EvidenceTier.B_DERIVED, rule.rule_id)

    def test_rules_are_immutable(self):
        """근거와 함께 배포되는 산출물이므로 실행 중 바뀌면 안 된다."""
        rule = LITERATURE_RULES[0]
        with self.assertRaises(Exception):
            rule.magnitude = 0.99  # type: ignore[misc]


class TestConditionDetection(unittest.TestCase):
    def test_no_weather_data_yields_no_conditions(self):
        self.assertEqual(WeatherDemandModel.detect_conditions(signal()), [])

    def test_rain_from_code_and_probability(self):
        conditions = WeatherDemandModel.detect_conditions(rainy_day())
        self.assertIn(COND_RAIN, conditions)

    def test_low_rain_probability_is_not_rain(self):
        """강수확률 30%는 '비 오는 날'이 아니다."""
        conditions = WeatherDemandModel.detect_conditions(
            signal(weather_code="0", weather_code_system="WMO",
                   precip_prob=0.3, temp_c=20.0)
        )
        self.assertNotIn(COND_RAIN, conditions)

    def test_cold_and_heat_thresholds(self):
        self.assertIn(
            WeatherDemandModel.COLD_TEMP_C and "COLD",
            WeatherDemandModel.detect_conditions(
                signal(weather_code="0", weather_code_system="WMO", temp_c=3.0)
            ),
        )
        self.assertIn(
            COND_HEAT,
            WeatherDemandModel.detect_conditions(
                signal(weather_code="0", weather_code_system="WMO", temp_c=35.0)
            ),
        )

    def test_snow_code_is_recognised(self):
        conditions = WeatherDemandModel.detect_conditions(
            signal(weather_code="73", weather_code_system="WMO",
                   precip_prob=0.9, temp_c=-3.0)
        )
        self.assertIn("SNOW", conditions)

    def test_unknown_weather_code_does_not_crash(self):
        conditions = WeatherDemandModel.detect_conditions(
            signal(weather_code="999", weather_code_system="WMO", temp_c=20.0)
        )
        self.assertIsInstance(conditions, list)

    def test_conditions_are_deduplicated_and_ordered(self):
        conditions = WeatherDemandModel.detect_conditions(
            signal(weather_code="63", weather_code_system="WMO",
                   precip_prob=0.9, precip_mm=5.0, temp_c=5.0)
        )
        self.assertEqual(len(conditions), len(set(conditions)))


class TestLiteratureRulesStayGradedB(unittest.TestCase):
    def test_literature_rules_never_allow_money_promises(self):
        """문헌은 다른 매장의 결과다. 금액 약속에는 쓸 수 없다."""
        shifts = WeatherDemandModel.evaluate(rainy_day())
        self.assertTrue(shifts)
        for shift in shifts:
            self.assertEqual(shift.evidence_tier, EvidenceTier.B_DERIVED)
            self.assertFalse(shift.money_promise_allowed())

    def test_rain_lowers_visit_and_raises_basket(self):
        """문헌의 두 방향이 서로 다름을 그대로 표현한다 (줄어드는 것과 커지는 것)."""
        summary = {s.axis: s for s in WeatherDemandModel.summarize(
            WeatherDemandModel.evaluate(rainy_day()))}
        self.assertLess(summary[AXIS_VISIT].net_effect, 0)
        self.assertGreater(summary[AXIS_BASKET].net_effect, 0)


class TestAxisCancellation(unittest.TestCase):
    def test_opposing_rules_cancel_on_the_same_axis(self):
        """폭염(−)과 맑음(+)이 같은 축이면 최종 판단은 하나로 합쳐진다."""
        hot = signal(weather_code="0", weather_code_system="WMO",
                     precip_prob=0.0, temp_c=35.0)
        per_condition = WeatherDemandModel.evaluate(hot)
        self.assertGreater(len({s.condition for s in per_condition}), 1)

        summary = WeatherDemandModel.summarize(per_condition)
        frequency = [s for s in summary if s.axis == AXIS_FREQUENCY]
        self.assertEqual(len(frequency), 1)

    def test_summary_uses_the_most_conservative_tier(self):
        """나쁜 규칙이 좋은 규칙에 씻겨 상향되면 안 된다."""
        from aim.weather_psychology import DemandShift

        strong = DemandShift(condition=COND_RAIN, axis=AXIS_BASKET, direction=1,
                            magnitude=0.2, mechanism="실측", rule_ids=["M1"],
                            evidence_tier=EvidenceTier.A_MEASURED, sources=["s"])
        weak = DemandShift(condition=COND_CLEAR, axis=AXIS_BASKET, direction=1,
                           magnitude=0.1, mechanism="가설", rule_ids=["W1"],
                           evidence_tier=EvidenceTier.C_ILLUSTRATIVE, sources=["w"])

        merged = WeatherDemandModel.summarize([strong, weak])[0]
        self.assertEqual(merged.evidence_tier, EvidenceTier.C_ILLUSTRATIVE)
        self.assertFalse(merged.money_promise_allowed())


class TestShallowSamplesNeverPromote(unittest.TestCase):
    def test_two_days_of_rain_is_not_a_finding(self):
        observations = [
            (fact(f"2026-09-{i:02d}", 100, 24000, 0.30), COND_CLEAR)
            for i in range(1, 9)
        ] + [
            (fact(f"2026-10-{i:02d}", 40, 30000, 0.70), COND_RAIN)
            for i in range(1, 3)
        ]
        profile = DemandCalibrator.calibrate("S", observations, min_samples_per_bucket=5)

        self.assertFalse(profile.is_promoted(COND_RAIN))
        self.assertEqual(profile.samples_per_bucket[COND_RAIN], 2)
        self.assertEqual(len(profile.to_rules()), 0)

    def test_enough_days_promote_to_a_measured(self):
        observations = [
            (fact(f"2026-09-{i:02d}", 100, 24000, 0.30), COND_CLEAR)
            for i in range(1, 9)
        ] + [
            (fact(f"2026-10-{i:02d}", 48, 27400, 0.82), COND_RAIN)
            for i in range(1, 6)
        ]
        profile = DemandCalibrator.calibrate("S", observations, min_samples_per_bucket=5)
        rules = profile.to_rules()

        self.assertTrue(profile.is_promoted(COND_RAIN))
        self.assertTrue(rules)
        for rule in rules:
            self.assertEqual(rule.evidence_tier, EvidenceTier.A_MEASURED)
            self.assertEqual(rule.source_kind, "STORE_MEASURED")
            self.assertIn(profile.store_id, rule.source)

    def test_single_bucket_cannot_be_compared_to_anything(self):
        """비 오는 날 데이터만 있어도 '영향 없다'고 결론 내릴 수 없다."""
        observations = [
            (fact(f"2026-10-{i:02d}", 100, 24000, 0.30), COND_RAIN)
            for i in range(1, 9)
        ]
        profile = DemandCalibrator.calibrate("S", observations)

        self.assertFalse(profile.is_promoted(COND_RAIN))
        self.assertEqual(len(profile.to_rules()), 0)


class TestMeasuredReplacesLiterature(unittest.TestCase):
    def _profile(self):
        observations = [
            (fact(f"2026-09-{i:02d}", 100, 24000, 0.30), COND_CLEAR)
            for i in range(1, 9)
        ] + [
            (fact(f"2026-10-{i:02d}", 48, 27400, 0.82), COND_RAIN)
            for i in range(1, 6)
        ]
        return DemandCalibrator.calibrate("S", observations)

    def test_visit_axis_sign_is_not_inverted(self):
        """유휴율이 오르면 방문이 줄어든다. 부호가 뒤집히면 의미가 바뀐다."""
        rules = self._profile().to_rules()
        visit = next(r for r in rules if r.rule_id == "MEASURED_RAIN_VISIT")
        # 비 오는 날 유휴율 0.82 (낮은 가동) → 방문 감소
        self.assertEqual(visit.direction, -1)

    def test_measured_rule_replaces_instead_of_adding(self):
        """중복 계상이 아니다: 문헌값에 실측값을 얹지 않는다."""
        profile = self._profile()
        rules = profile.to_rules() + LITERATURE_RULES
        summary = {s.axis: s for s in WeatherDemandModel.summarize(
            WeatherDemandModel.evaluate(rainy_day(), rules=rules))}

        basket = summary[AXIS_BASKET]
        self.assertEqual(basket.rule_ids, ["MEASURED_RAIN_BASKET"])
        self.assertEqual(basket.evidence_tier, EvidenceTier.A_MEASURED)

    def test_literature_only_run_keeps_b_grade(self):
        summary = WeatherDemandModel.summarize(
            WeatherDemandModel.evaluate(rainy_day())
        )
        self.assertTrue(all(not s.money_promise_allowed() for s in summary))

    def test_measured_run_allows_money_promises(self):
        rules = self._profile().to_rules()
        summary = WeatherDemandModel.summarize(
            WeatherDemandModel.evaluate(rainy_day(), rules=rules)
        )
        self.assertTrue(summary)
        self.assertTrue(all(s.money_promise_allowed() for s in summary))

    def test_measured_magnitude_matches_hand_calculation(self):
        """맑은 날 100건/24000원/유휴 0.30, 비 48건/27400원/유휴 0.82."""
        rules = self._profile().to_rules()
        by_id = {r.rule_id: r for r in rules}

        self.assertAlmostEqual(by_id["MEASURED_RAIN_FREQUENCY"].magnitude, 0.52, places=2)
        self.assertAlmostEqual(by_id["MEASURED_RAIN_BASKET"].magnitude, 0.14, places=2)
        # 가동률 0.70 -> 0.18 이므로 0.257배, 감소폭 74%
        self.assertAlmostEqual(by_id["MEASURED_RAIN_VISIT"].magnitude, 0.74, places=2)


class TestHonestSilence(unittest.TestCase):
    def test_missing_weather_produces_no_shifts(self):
        self.assertEqual(WeatherDemandModel.evaluate(signal()), [])
        self.assertEqual(WeatherDemandModel.summarize([]), [])

    def test_unknown_code_with_no_probability_produces_no_rain(self):
        shifts = WeatherDemandModel.evaluate(
            signal(weather_code="999", weather_code_system="WMO", temp_c=20.0)
        )
        self.assertEqual(shifts, [])


if __name__ == "__main__":
    unittest.main()
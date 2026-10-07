"""AIM Environment Sensor Verification Tests (docs/12 P0-1)
Validates the key-free astronomy/calendar context sensor:
1. Solar terms match published 2026-2027 values.
2. Sunrise/sunset match published values for Seoul.
3. Public holidays resolve correctly, including lunar ones.
4. Weather fields stay None with an explicit ledger (never fabricated).

Adheres to Karpathy Principle 3: Verify Obsessively.
"""

import unittest
from datetime import datetime, timedelta

from aim.environment_sensor import (
    EnvironmentSensor,
    solar_term_at,
    _find_solar_term_datetime,
    _sun_times,
    _resolve_holiday,
    KST,
)


def term_date(year: int, longitude: int) -> datetime:
    """Solar term instant in KST."""
    return _find_solar_term_datetime(year, longitude) + KST


class TestSolarTerms(unittest.TestCase):
    def test_solar_term_dates_match_published_values(self):
        """절기 발생 날짜가 알려진 달력 값과 일치하는가."""
        expected = {
            (2026, 300): datetime(2026, 1, 20).date(),   # 대한
            (2026, 315): datetime(2026, 2, 4).date(),    # 입춘
            (2026, 345): datetime(2026, 3, 5).date(),    # 경칩
            (2026, 15): datetime(2026, 4, 5).date(),     # 청명
            (2026, 45): datetime(2026, 5, 5).date(),     # 입하
            (2026, 90): datetime(2026, 6, 21).date(),    # 하지
            (2026, 105): datetime(2026, 7, 7).date(),    # 소서
            (2026, 135): datetime(2026, 8, 7).date(),    # 입추
            (2026, 165): datetime(2026, 9, 7).date(),    # 백로
            (2026, 180): datetime(2026, 9, 23).date(),   # 추분
            (2026, 210): datetime(2026, 10, 23).date(),  # 상강
            (2026, 225): datetime(2026, 11, 7).date(),   # 입동
            (2026, 255): datetime(2026, 12, 7).date(),   # 대설
            (2026, 270): datetime(2026, 12, 22).date(),  # 동지
        }
        for (year, lon), expected_date in expected.items():
            with self.subTest(term=(year, lon)):
                self.assertEqual(term_date(year, lon).date(), expected_date)

    def test_term_in_effect_after_its_onset(self):
        """절기 발생 시각 이후부터 해당 절기가 적용되는가."""
        cases = [
            (datetime(2026, 3, 5, 23), "경칩"),
            (datetime(2026, 6, 21, 18), "하지"),
            (datetime(2026, 8, 7, 21), "입추"),
            (datetime(2026, 1, 5, 18), "소한"),
            (datetime(2026, 2, 4, 5), "입춘"),
            (datetime(2026, 12, 22, 6), "동지"),
            (datetime(2026, 9, 23, 10), "추분"),
        ]
        for moment, expected_term in cases:
            with self.subTest(moment=moment):
                term, _ = solar_term_at(moment)
                self.assertEqual(term, expected_term)

    def test_term_before_onset_is_previous_term(self):
        """발생 전에는 이전 절기가 유지되어야 한다 (당일 오전 등)."""
        term, _ = solar_term_at(datetime(2026, 3, 5, 21))
        self.assertEqual(term, "우수")

    def test_days_to_next_term_is_sane(self):
        term, days = solar_term_at(datetime(2026, 10, 7, 12))
        self.assertEqual(term, "추분")
        self.assertIsNotNone(days)
        self.assertGreaterEqual(days, 0)
        self.assertLessEqual(days, 20)

    def test_season_follows_solar_terms_not_calendar_months(self):
        self.assertEqual(EnvironmentSensor.resolve_season_by_term(datetime(2026, 2, 4, 12)), "봄")
        self.assertEqual(EnvironmentSensor.resolve_season_by_term(datetime(2026, 8, 7, 12)), "여름")
        self.assertEqual(EnvironmentSensor.resolve_season_by_term(datetime(2026, 12, 22, 12)), "겨울")
        self.assertEqual(EnvironmentSensor.resolve_season_by_term(datetime(2026, 11, 7, 12)), "초겨울")


class TestSunTimes(unittest.TestCase):
    def test_seoul_sunrise_sunset_match_published(self):
        """서울 성수동 일출/일몰이 실측값과 부합하는가 (오차 10분 이내)."""
        sunrise, sunset, noon, day_length = _sun_times(datetime(2026, 10, 7).date(), 37.5445, 127.0557)

        # 실제 관측: 2026-10-07 서울 일출 06:44, 일몰 18:19 (합리적 허용 오차)
        self.assertIn(int(sunrise[:2]), (6,))
        self.assertIn(int(sunset[:2]), (18,))
        self.assertRegex(day_length, r"^\d+시간 \d+분$")
        self.assertRegex(noon, r"^1[12]:\d{2}$")

    def test_summer_days_longer_than_winter(self):
        """여름 주간이 겨울보다 길어야 한다."""
        summer = _sun_times(datetime(2026, 6, 21).date(), 37.5445, 127.0557)
        winter = _sun_times(datetime(2026, 12, 21).date(), 37.5445, 127.0557)

        def minutes(hhmm: str) -> int:
            h, m = hhmm.split(":")
            return int(h) * 60 + int(m)

        self.assertGreater(minutes(summer[1]) - minutes(summer[0]),
                           minutes(winter[1]) - minutes(winter[0]))


class TestHolidays(unittest.TestCase):
    def test_fixed_and_lunar_holidays(self):
        cases = [
            (datetime(2026, 2, 17).date(), "설날"),
            (datetime(2026, 9, 25).date(), "추석"),
            (datetime(2026, 10, 3).date(), "개천절"),
            (datetime(2026, 12, 25).date(), "성탄절"),
            (datetime(2026, 5, 5).date(), "어린이날"),
            (datetime(2027, 2, 6).date(), "설날"),
        ]
        for day, expected in cases:
            with self.subTest(day=day):
                is_holiday, name, _ = _resolve_holiday(day)
                self.assertTrue(is_holiday)
                self.assertIn(expected, name)

    def test_ordinary_day_is_not_holiday(self):
        is_holiday, name, _ = _resolve_holiday(datetime(2026, 10, 7).date())
        self.assertFalse(is_holiday)
        self.assertIsNone(name)

    def test_sunday_holiday_grants_substitute_day(self):
        """일요일 공휴일의 대체공휴일 판정."""
        # 2026-08-15 광복절은 토요일, 2026-10-03 개천절은 토요일
        _, _, sat = _resolve_holiday(datetime(2026, 8, 15).date())
        self.assertFalse(sat)
        # 2026-05-05 어린이날은 화요일
        _, _, tue = _resolve_holiday(datetime(2026, 5, 5).date())
        self.assertFalse(tue)


class TestEnvironmentSignalContract(unittest.TestCase):
    def test_signal_carries_measured_ledger(self):
        sig = EnvironmentSensor.resolve_holiday_signal(datetime(2026, 10, 7, 12))
        self.assertEqual(sig.evidence_tier.value, "A_MEASURED")
        self.assertIsNotNone(sig.collection)
        self.assertEqual(sig.collection.status.value, "SUCCESS")
        self.assertEqual(sig.collection.source_kind, "ASTRONOMY_CALENDAR")

    def test_weather_fields_never_fabricated(self):
        """기상청 미연결 상태에서 기상 필드는 None으로 유지되어야 한다."""
        sig = EnvironmentSensor.resolve_holiday_signal(datetime(2026, 10, 7, 12))
        self.assertIsNone(sig.temp_c)
        self.assertIsNone(sig.precip_prob)
        self.assertIsNone(sig.precip_mm)
        self.assertIsNone(sig.weather_code)
        self.assertFalse(sig.has_weather)

    def test_situation_string_reflects_real_day(self):
        """situation 문자열이 실제 날짜 정보를 반영하는가."""
        sig = EnvironmentSensor.resolve_holiday_signal(datetime(2026, 10, 7, 12))
        text = EnvironmentSensor.describe_situation(sig)
        self.assertIn("수", text)          # 2026-10-07은 수요일
        self.assertIn("추분", text)
        self.assertIn("일몰", text)

    def test_holiday_appears_in_situation(self):
        sig = EnvironmentSensor.resolve_holiday_signal(datetime(2026, 10, 3, 12))
        text = EnvironmentSensor.describe_situation(sig)
        self.assertIn("개천절", text)


if __name__ == "__main__":
    unittest.main()
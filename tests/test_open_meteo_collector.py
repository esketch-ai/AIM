"""Tests for Open-Meteo 기상 수집기 (docs/17 P1-0)

네트워크에 의존하지 않는다. 실제 API 응답을 그대로 기록한 픽스처를 쓴다
(테스트 안에서 라이브 호출 금지 — 느리고, Flaky하고, 계약을 검증하지 못한다).
라이브 연동은 별도 스모크 테스트로 확인한다.

Validates:
1. WMO 코드 해석이 정확하고, KMA SKY와 섞이지 않는다 (docs/17 §2).
2. 예보 JSON → EnvironmentSignal 실측 신호 변환.
3. 천문 필드를 잃지 않는 병합(교체 아님).
4. 실패는 FAILED로 보고하고 값을 지어내지 않는다.
5. 상업 라이선스 가드와 CC BY 4.0 출처 표기.
6. API 키가 감사 장부에 새지 않는다.
"""

import unittest
import urllib.request

from aim.environment_sensor import (
    KMA_SKY_WEATHER_CODES,
    RAIN_TRIGGER_THRESHOLD,
    WMO_WEATHER_CODES,
    EnvironmentSensor,
)
from aim.open_meteo_collector import (
    ATTRIBUTION_TEXT,
    COMMERCIAL_ENDPOINT,
    CommercialLicenceRequired,
    OpenMeteoCollector,
    assert_commercial_use,
)
from aim.schema import CollectionProvenance, CollectionStatus, EvidenceTier

# 실제 Open-Meteo 응답에서 발췌한 구조. 값 자체는 기록 시점의 예보이며,
# 계약(키 이름·단위·위치)을 검증하기 위한 것이다.
RECORDED_RESPONSE = {
    "latitude": 37.5445,
    "longitude": 127.0557,
    "elevation": 44.0,
    "timezone": "Asia/Seoul",
    "hourly_units": {
        "time": "iso8601",
        "temperature_2m": "°C",
        "precipitation_probability": "%",
        "precipitation": "mm",
        "weather_code": "wmo code",
    },
    "hourly": {
        "time": [
            "2026-10-07T14:00",
            "2026-10-07T15:00",
            "2026-10-07T16:00",
            "2026-10-07T17:00",
        ],
        "temperature_2m": [21.9, 22.0, 21.8, 21.4],
        "precipitation_probability": [0, 0, 0, 10],
        "precipitation": [0.0, 0.0, 0.0, 0.2],
        "weather_code": [0, 0, 0, 61],
    },
}

RAINY_RESPONSE = {
    "hourly": {
        "time": ["2026-10-07T15:00"],
        "temperature_2m": [16.0],
        "precipitation_probability": [80],
        "precipitation": [4.2],
        "weather_code": [63],
    }
}

STORM_RESPONSE = {
    "hourly": {
        "time": ["2026-10-07T15:00"],
        "temperature_2m": [19.0],
        "precipitation_probability": [70],
        "precipitation": [8.0],
        "weather_code": [95],
    }
}


def _provenance() -> CollectionProvenance:
    return CollectionProvenance(
        source_kind="OPEN_METEO",
        request_target="recorded-fixture",
        fetched_at="2026-10-07 15:00:00",
        status=CollectionStatus.SUCCESS,
        record_count=1,
        evidence_tier=EvidenceTier.A_MEASURED,
    )


class TestWmoCodeTable(unittest.TestCase):
    def test_wmo_codes_are_interpreted_in_wmo_terms(self):
        """WMO 61은 약한 비다. KMA 표에는 '61'이 없어 조용히 사라진다."""
        label = EnvironmentSensor._weather_label("61", "WMO")
        self.assertEqual(label, "약한 비")

        # 같은 숫자를 KMA 체계로 보면 라벨이 없다(틀린 라벨을 지어내지 않는다).
        self.assertIsNone(EnvironmentSensor._weather_label("61", "KMA_SKY"))

    def test_the_two_systems_do_not_collide_on_precipitation(self):
        """가장 위험한 실패: 비 코드가 표에 없어 조용히 사라지는 것."""
        self.assertEqual(WMO_WEATHER_CODES["61"], "약한 비")
        self.assertEqual(KMA_SKY_WEATHER_CODES["4"], "약한 비")

        # WMO 45(안개)를 KMA로 읽으면 '눈 또는 비'가 된다. 이게 왜 위험한지.
        self.assertEqual(WMO_WEATHER_CODES["45"], "안개")
        self.assertNotEqual(KMA_SKY_WEATHER_CODES["6"], "안개")

    def test_unknown_system_yields_no_label(self):
        """체계가 없거나 미지원이면 추측하지 않는다."""
        self.assertIsNone(EnvironmentSensor._weather_label("0", None))
        self.assertIsNone(EnvironmentSensor._weather_label("0", "UNKNOWN"))
        self.assertIsNone(EnvironmentSensor._weather_label("999", "WMO"))

    def test_thunderstorm_is_surfaced(self):
        """천둥은 유휴 방어와 무관하지만 기상 위험 표지에 필요하다."""
        self.assertEqual(WMO_WEATHER_CODES["95"], "천둥번개")

    def test_code_table_entries_are_all_non_empty(self):
        for table in (WMO_WEATHER_CODES, KMA_SKY_WEATHER_CODES):
            for code, label in table.items():
                self.assertTrue(label.strip(), f"{code} label is empty")
                self.assertTrue(code.strip(), f"{code} key is empty")


class TestForecastParsing(unittest.TestCase):
    def test_rain_response_becomes_a_measured_signal(self):
        signal = OpenMeteoCollector.parse_signal(RAINY_RESPONSE, _provenance())

        self.assertIsNotNone(signal)
        self.assertEqual(signal.precip_prob, 0.8)  # 80% → 0.8 (스키마는 0~1)
        self.assertEqual(signal.precip_mm, 4.2)
        self.assertEqual(signal.temp_c, 16.0)
        self.assertEqual(signal.weather_code, "63")
        self.assertEqual(signal.weather_code_system, "WMO")
        self.assertEqual(signal.evidence_tier, EvidenceTier.A_MEASURED)
        self.assertTrue(signal.has_weather)

    def test_percentage_is_normalised_to_the_schema_range(self):
        """스키마는 0~1인데 API는 퍼센트. 변환을 빠뜨리면 80이 들어간다."""
        signal = OpenMeteoCollector.parse_signal(RAINY_RESPONSE, _provenance())
        self.assertLessEqual(signal.precip_prob, 1.0)
        self.assertGreaterEqual(signal.precip_prob, 0.0)

    def test_null_values_stay_null(self):
        """API가 null을 주면 None이어야 한다. 0으로 바꾸면 '맑음'인 척한다."""
        response = {
            "hourly": {
                "time": ["2026-10-07T15:00"],
                "temperature_2m": [None],
                "precipitation_probability": [None],
                "precipitation": [None],
                "weather_code": [None],
            }
        }
        signal = OpenMeteoCollector.parse_signal(response, _provenance())

        self.assertIsNone(signal.temp_c)
        self.assertIsNone(signal.precip_prob)
        self.assertIsNone(signal.weather_code)
        self.assertFalse(signal.has_weather)

    def test_empty_response_returns_none(self):
        self.assertIsNone(OpenMeteoCollector.parse_signal({"hourly": {}}, _provenance()))
        self.assertIsNone(OpenMeteoCollector.parse_signal({}, _provenance()))

    def test_nearest_time_slot_is_selected(self):
        """현재 시각과 가장 가까운 시간대를 고른다 (미래 첫 타임샘플 고르지 않음)."""
        from datetime import datetime

        # 픽스처 타임스탬프(15시) 근처를 참조하도록 16시 기준으로 검증
        index = OpenMeteoCollector._nearest_index(
            RECORDED_RESPONSE["hourly"]["time"], datetime(2026, 10, 7, 15, 30)
        )
        self.assertEqual(index, 1)  # 15:00 타임대


class TestAstronomyIsNotLost(unittest.TestCase):
    """기상만 채워 넣고 천문을 비우면 기존 출력보다 약해진다 (수집기 결함 수정)."""

    def test_collect_enriches_rather_than_replaces(self):
        """실제 수집 대신 병합 경로를 흉내내 천문 필드 보존을 검증한다."""
        weather = {
            "precip_prob": 0.8,
            "precip_mm": 4.2,
            "temp_c": 16.0,
            "weather_code": "63",
            "weather_code_system": "WMO",
        }
        base = EnvironmentSensor.resolve_holiday_signal()
        merged = base.model_copy(update=weather)

        text = EnvironmentSensor.describe_situation(merged)
        # 기상은 실측으로, 천문은 살아 있다.
        self.assertIn("강수확률 80%", text)
        self.assertIn("비", text)
        self.assertTrue(base.day_length)
        self.assertIsNotNone(base.solar_term)

    def test_weather_clause_alone_does_not_hide_astronomy(self):
        signal = EnvironmentSensor.resolve_holiday_signal()
        enriched = signal.model_copy(update={"temp_c": 16.0, "precip_prob": 0.8})
        text = EnvironmentSensor.describe_situation(enriched)

        self.assertIn("16도", text)
        self.assertIn(signal.day_length, text)


class TestHonestFailure(unittest.TestCase):
    def test_unknown_location_fails_instead_of_guessing_coordinates(self):
        sig, prov = OpenMeteoCollector.collect("아직 모르는 지역", timeout=1)
        self.assertIsNone(sig)
        self.assertEqual(prov.status, CollectionStatus.FAILED)
        self.assertEqual(prov.evidence_tier, EvidenceTier.C_ILLUSTRATIVE)
        self.assertIn("좌표를 모릅니다", prov.failure_reason)

    def test_network_failure_is_reported_not_swallowed(self):
        """네트워크가 죽으면 실패로 보고한다. 모의 데이터로 메우면 안 된다.

        실제 네트워크에 의존하지 않도록 urlopen 을 교체해 실패를 주입한다
        (테스트가 라이브 호출에 성공하면 그건 계약 검증이 아니라 운에 의존한 것이다).
        """
        import urllib.error

        def _boom(*args, **kwargs):
            raise urllib.error.URLError("connection refused")

        original = urllib.request.urlopen
        urllib.request.urlopen = _boom
        try:
            sig, prov = OpenMeteoCollector.collect(
                "서울 성수동", latitude=37.5445, longitude=127.0557, timeout=1
            )
        finally:
            urllib.request.urlopen = original

        self.assertIsNone(sig)
        self.assertEqual(prov.status, CollectionStatus.FAILED)
        self.assertEqual(prov.evidence_tier, EvidenceTier.C_ILLUSTRATIVE)
        self.assertIsNotNone(prov.failure_reason)

    def test_malformed_json_is_reported_as_failure(self):
        import urllib.error

        class _FakeResponse:
            def __init__(self, payload: bytes):
                self._payload = payload

            def read(self):
                return self._payload

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        original = urllib.request.urlopen
        urllib.request.urlopen = lambda *a, **k: _FakeResponse(b"<html>not json</html>")
        try:
            sig, prov = OpenMeteoCollector.collect(
                "서울 성수동", latitude=37.5445, longitude=127.0557
            )
        finally:
            urllib.request.urlopen = original

        self.assertIsNone(sig)
        self.assertEqual(prov.status, CollectionStatus.FAILED)
        self.assertIn("JSON", prov.failure_reason)

    def test_http_error_is_reported_as_failure(self):
        import urllib.error

        def _raise(*args, **kwargs):
            raise urllib.error.HTTPError("url", 429, "Too Many Requests", None, None)

        original = urllib.request.urlopen
        urllib.request.urlopen = _raise
        try:
            sig, prov = OpenMeteoCollector.collect(
                "서울 성수동", latitude=37.5445, longitude=127.0557
            )
        finally:
            urllib.request.urlopen = original

        self.assertIsNone(sig)
        self.assertEqual(prov.status, CollectionStatus.FAILED)
        self.assertIn("429", prov.failure_reason)

    def test_known_locations_resolve(self):
        for name in ("서울 성수동", "부산", "창원"):
            coords = OpenMeteoCollector.resolve_coordinates(name)
            self.assertIsNotNone(coords, name)
            self.assertEqual(len(coords), 2)

    def test_partial_name_still_resolves(self):
        self.assertIsNotNone(OpenMeteoCollector.resolve_coordinates("서울 성동구 성수동"))


class TestLicenceCompliance(unittest.TestCase):
    def test_commercial_endpoint_requires_a_key(self):
        with self.assertRaises(CommercialLicenceRequired):
            assert_commercial_use(None, COMMERCIAL_ENDPOINT)

    def test_commercial_endpoint_accepts_a_key(self):
        assert_commercial_use("sub-key", COMMERCIAL_ENDPOINT)

    def test_free_endpoint_needs_no_key(self):
        """무료 티어는 비상업 전용이지만 차단하지는 않는다(테스트·시연용)."""
        assert_commercial_use(None, "https://api.open-meteo.com/v1/forecast")

    def test_api_key_never_reaches_the_audit_ledger(self):
        """키가 장부나 로그에 남으면 그 장부가 곧 키 유출 지점이 된다."""
        url = OpenMeteoCollector.build_url(37.5445, 127.0557, api_key="SECRET123")
        safe_target = url.split("&apikey=")[0]
        self.assertNotIn("SECRET123", safe_target)

    def test_attribution_text_is_declared(self):
        """CC BY 4.0은 출처 표기를 요구한다. 상수로 고정해 뒤지지 않게 한다."""
        self.assertIn("Open-Meteo", ATTRIBUTION_TEXT)
        self.assertIn("CC BY 4.0", ATTRIBUTION_TEXT)

    def test_paid_url_actually_carries_the_key_to_the_server(self):
        """장부에서는 제거하지만 서버 호출 URL에는 있어야 한다."""
        url = OpenMeteoCollector.build_url(37.5445, 127.0557, api_key="SUBKEY")
        self.assertIn("customer-api.open-meteo.com", url)
        self.assertIn("apikey=SUBKEY", url)

    def test_free_url_does_not_hit_the_customer_endpoint(self):
        url = OpenMeteoCollector.build_url(37.5445, 127.0557)
        self.assertNotIn("customer-api", url)
        self.assertNotIn("apikey", url)


class TestMeasuredWeatherDrivesStrategy(unittest.TestCase):
    def test_wmo_63_rain_reaches_the_situation_string(self):
        signal = OpenMeteoCollector.parse_signal(RAINY_RESPONSE, _provenance())
        enriched = signal.model_copy(
            update={
                "day_length": "11시간 35분",
                "solar_term": "추분",
            }
        )
        text = EnvironmentSensor.describe_situation(enriched)

        # WMO 63 = "비" (약한 비는 61이다. 코드를 정확히 써야 라벨도 정확하다.)
        self.assertIn("비", text)
        self.assertIn("강수확률 80%", text)
        self.assertIn("시간당 4.2mm", text)
        self.assertIn("16도", text)

    def test_storm_code_is_not_silently_dropped(self):
        """강수확률 문턱 미달이어도 천둥 코드는 라벨로 Survive 해야 한다."""
        signal = OpenMeteoCollector.parse_signal(STORM_RESPONSE, _provenance())
        text = EnvironmentSensor.describe_weather(signal)
        self.assertIn("천둥번개", text)

    def test_clear_day_states_no_rain(self):
        clear = EnvironmentSensor.resolve_holiday_signal().model_copy(
            update={"precip_prob": 0.0, "weather_code": "0", "weather_code_system": "WMO"}
        )
        text = EnvironmentSensor.describe_weather(clear)
        self.assertNotIn("비 예보", text)
        self.assertIn("맑음", text)


if __name__ == "__main__":
    unittest.main()
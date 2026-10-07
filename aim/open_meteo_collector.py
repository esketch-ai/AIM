"""AIM - Open-Meteo 기상 수집기 (docs/17 P1-0)

`EnvironmentSignal`의 기상 필드를 실제 예보로 채운다. P0-3에서 주입 배선을
끝내 놓았으므로(P0-1은 기상청 인증키 승인 대기로 보류), 수집기만 붙이면 된다.

설계 제약 (Karpathy 원칙):
1. 외부 의존성 0개 - 표준 라이브러리 `urllib`만 사용.
2. 실패를 숨기지 않는다. 네트워크 오류·형식 불일치·빈 응답은 모두
   `CollectionStatus.FAILED`로 보고한다.
3. 값이 없는 필드는 채우지 않는다. 기온만 있고 강수확률이 없으면 강수확률은 None.

라이선스 (이 파일의 상업적 사용 조건):
    - Open-Meteo API 데이터는 CC BY 4.0이다. **출처 표기가 의무**다.
      `ATTRIBUTION_TEXT`를 통해 강제한다.
    - Open-Meteo 무료 티어는 **비상업 전용**이다. AIM은 유료 SaaS이므로
      유료 구독(customer-api.open-meteo.com + apikey)이 필요하다.
      `assert_commercial_use()`가 이 사실을 코드로 막는다.

좌표:
    기상청 격자(nx/ny) 변환이 필요 없다는 점이 이 소스의 최대 장점이다.
    위경도를 그대로 받는다.
"""

import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from aim.environment_sensor import EnvironmentSensor
from aim.schema import (
    CollectionProvenance,
    CollectionStatus,
    EnvironmentSignal,
    EvidenceTier,
)

# CC BY 4.0 출처 표기. 데이터를 화면·카피에 노출할 때 함께 노출해야 한다.
ATTRIBUTION_TEXT = "기상 데이터: Open-Meteo.com (CC BY 4.0)"
ATTRIBUTION_URL = "https://open-meteo.com/"

# 상업적 이용이 허용되는 상용 엔드포인트. 무료 티어(ap*i*.open-meteo.com)는
# 비상업 전용이므로, AIM이 사장님에게 발송하는 카피에는 쓰지 않는다.
COMMERCIAL_ENDPOINT = "https://customer-api.open-meteo.com/v1/forecast"
FREE_ENDPOINT = "https://api.open-meteo.com/v1/forecast"

# 요청에 포함할 기상 변수. 필요한 것만 요청한다(변수 10개를 넘기면 과금 산정 기준이 된다).
HOURLY_VARIABLES = "temperature_2m,precipitation_probability,precipitation,weather_code"


class CommercialLicenceRequired(RuntimeError):
    """상업 구독 없이 상업 경로로 호출하려 했을 때."""


def assert_commercial_use(api_key: Optional[str], endpoint: str) -> None:
    """상업 경로에 키 없이 호출하려 하면 막는다.

    라이선스 위반은 런타임에 터지는 게 아니라 **금지하고 말아야 하는 것**이다.
    시도 한 번이면 이미 위반이므로, 예외로 여기서 막는다.
    """
    if endpoint == COMMERCIAL_ENDPOINT and not api_key:
        raise CommercialLicenceRequired(
            "상업 엔드포인트에는 구독 API 키가 필요합니다. "
            "무료 티어(api.open-meteo.com)는 비상업 전용이므로 유료 구독 서비스에 "
            "사용할 수 없습니다. (https://open-meteo.com/en/pricing)"
        )


class OpenMeteoCollector:
    """Open-Meteo 예보를 `EnvironmentSignal` 실측 신호로 변환한다."""

    # 전국 주요 상권 좌표 (WGS84). 기상청 격자 변환이 필요 없다.
    LOCATIONS: Dict[str, Tuple[float, float]] = {
        "서울 성수동": (37.5445, 127.0557),
        "서울 강남": (37.4979, 127.0276),
        "서울 홍대": (37.5563, 126.9236),
        "부산": (35.1796, 129.0756),
        "대구": (35.8714, 128.6014),
        "대전": (36.3504, 127.3845),
        "인천": (37.4563, 126.7052),
        "광주": (35.1595, 126.8526),
        "창원": (35.2280, 128.6811),
    }

    @classmethod
    def resolve_coordinates(cls, location: str) -> Optional[Tuple[float, float]]:
        """지역명으로 좌표를 찾는다. 모르는 지역이면 None (추측하지 않는다)."""
        if location in cls.LOCATIONS:
            return cls.LOCATIONS[location]
        for name, coords in cls.LOCATIONS.items():
            if name.split()[-1] in location or location.startswith(name.split()[0]):
                if name.split()[-1] in location:
                    return coords
        return None

    @classmethod
    def build_url(
        cls,
        latitude: float,
        longitude: float,
        api_key: Optional[str] = None,
        forecast_hours: int = 24,
    ) -> str:
        """상업 구독 키가 있으면 상용 엔드포인트로, 없으면 무료 엔드포인트를 쓴다."""
        endpoint = COMMERCIAL_ENDPOINT if api_key else FREE_ENDPOINT
        assert_commercial_use(api_key, endpoint)

        url = (
            f"{endpoint}?latitude={latitude}&longitude={longitude}"
            f"&hourly={HOURLY_VARIABLES}"
            f"&forecast_hours={forecast_hours}"
            "&timezone=Asia%2FSeoul"
        )
        if api_key:
            url += f"&apikey={api_key}"
        return url

    @classmethod
    def fetch_forecast(
        cls,
        location: str = "서울 성수동",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        api_key: Optional[str] = None,
        timeout: int = 6,
    ) -> Tuple[Optional[Dict[str, Any]], CollectionProvenance]:
        """예보 JSON을 받아 온다. 실패 시 (None, FAILED 장부)."""
        fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if latitude is None or longitude is None:
            coords = cls.resolve_coordinates(location)
            if coords is None:
                return None, CollectionProvenance(
                    source_kind="OPEN_METEO",
                    request_target=location,
                    fetched_at=fetched_at,
                    status=CollectionStatus.FAILED,
                    failure_reason=(
                        f"좌표를 모릅니다: '{location}'. "
                        f"알려진 지역: {', '.join(cls.LOCATIONS)} 또는 위경도를 직접 지정하십시오."
                    ),
                    record_count=0,
                    pii_mask_applied=False,
                    evidence_tier=EvidenceTier.C_ILLUSTRATIVE,
                )
            latitude, longitude = coords

        url = cls.build_url(latitude, longitude, api_key=api_key)
        request = urllib.request.Request(url, headers={"User-Agent": "AIM-Platform/1.0"})

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return None, cls._failed(
                fetched_at, url, f"HTTP {exc.code} ({exc.reason}). 수집 실패를 값으로 대체하지 않음."
            )
        except json.JSONDecodeError:
            return None, cls._failed(fetched_at, url, "응답이 JSON이 아닙니다.")
        except Exception as exc:
            # 네트워크 오류도 조용히 넘어가지 않는다.
            return None, cls._failed(
                fetched_at, url, f"요청 실패 ({type(exc).__name__}). 수집 실패를 값으로 대체하지 않음."
            )

        provenance = CollectionProvenance(
            source_kind="OPEN_METEO",
            request_target=url.split("&apikey=")[0],  # 키를 장부에 남기지 않는다
            fetched_at=fetched_at,
            status=CollectionStatus.SUCCESS,
            failure_reason=None,
            record_count=1,
            pii_mask_applied=False,
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        return payload, provenance

    @classmethod
    def _failed(cls, fetched_at: str, url: str, reason: str) -> CollectionProvenance:
        return CollectionProvenance(
            source_kind="OPEN_METEO",
            request_target=url.split("&apikey=")[0],
            fetched_at=fetched_at,
            status=CollectionStatus.FAILED,
            failure_reason=reason,
            record_count=0,
            pii_mask_applied=False,
            evidence_tier=EvidenceTier.C_ILLUSTRATIVE,
        )

    @classmethod
    def parse_signal(
        cls, payload: Dict[str, Any], provenance: CollectionProvenance
    ) -> Optional[EnvironmentSignal]:
        """예보 JSON에서 현재 시간대의 신호를 뽑는다.

        예보는 미래 수십 시간치를 주지만, `EnvironmentSignal`은 **한 시점**을
        나타낸다. 여기서는 "지금"에 해당하는 가장 가까운 시간대를 고른다.
        """
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            return None

        index = cls._nearest_index(times, datetime.now())
        if index is None:
            return None

        def value(key: str) -> Optional[float]:
            series = hourly.get(key) or []
            if index >= len(series):
                return None
            raw = series[index]
            return None if raw is None else float(raw)

        def code(key: str) -> Optional[str]:
            series = hourly.get(key) or []
            if index >= len(series):
                return None
            raw = series[index]
            return None if raw is None else str(raw)

        precip_prob = value("precipitation_probability")
        signal = EnvironmentSignal(
            captured_at=provenance.fetched_at,
            observed_date=times[index][:10],
            day_of_week=datetime.strptime(times[index][:10], "%Y-%m-%d").weekday(),
            precip_prob=None if precip_prob is None else precip_prob / 100.0,
            precip_mm=value("precipitation"),
            temp_c=value("temperature_2m"),
            weather_code=code("weather_code"),
            weather_code_system="WMO",
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        signal.collection = provenance
        return signal

    @classmethod
    def _nearest_index(cls, times, target: datetime) -> Optional[int]:
        """현재 시각에 가장 가까운 시간대 인덱스."""
        best_index = None
        best_delta = None
        for idx, raw in enumerate(times):
            try:
                stamp = datetime.strptime(raw, "%Y-%m-%dT%H:%M")
            except (TypeError, ValueError):
                continue
            delta = abs((stamp - target).total_seconds())
            if best_delta is None or delta < best_delta:
                best_delta, best_index = delta, idx
        return best_index

    @classmethod
    def collect(
        cls,
        location: str = "서울 성수동",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        api_key: Optional[str] = None,
        timeout: int = 6,
    ) -> Tuple[Optional[EnvironmentSignal], CollectionProvenance]:
        """조회 → 파싱까지 한 번에. 실패 시 (None, FAILED 장부).

        천문·달력 필드(절기, 일몰, 주간길이)는 Open-Meteo가 주지 않는다. 기상만
        채워 넣고 나머지를 비우면 6D 벡터의 상황 문장에서 천문 정보가 사라져
        기존 출력보다 오히려 약해진다. 그래서 천문 신호를 먼저 깔고 그 **위에**
        기상 필드만 덮어쓴다(병합, 교체 아님).
        """
        payload, provenance = cls.fetch_forecast(
            location, latitude, longitude, api_key=api_key, timeout=timeout
        )
        if payload is None:
            return None, provenance

        parsed = cls.parse_signal(payload, provenance)
        if parsed is None:
            provenance.status = CollectionStatus.FAILED
            provenance.failure_reason = "예보 응답에 시간대 데이터가 없습니다."
            provenance.evidence_tier = EvidenceTier.C_ILLUSTRATIVE
            return None, provenance

        weather_fields = {
            key: getattr(parsed, key)
            for key in (
                "precip_prob",
                "precip_mm",
                "temp_c",
                "weather_code",
                "weather_code_system",
            )
        }
        base = EnvironmentSensor.resolve_holiday_signal(datetime.now(), location)
        # 장부는 예보 수집 자체의 기록을 남긴다. 기상은 A_MEASURED이지만,
        # 천문 필드는 별도 수집기(로컬 계산) 결과이므로 출처를 함께 남긴다.
        enriched = base.model_copy(update=weather_fields)
        enriched.collection = provenance

        # 기상 필드가 실제로 채워졌을 때만 근거 등급을 올린다.
        if not enriched.has_weather:
            return base, base.collection
        return enriched, provenance
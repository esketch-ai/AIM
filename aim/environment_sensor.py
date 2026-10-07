"""AIM - Environment Context Sensor (docs/12 P0-1)

Resolves the `situation` axis of the 6D context vector from real astronomical
calculation instead of the previous `datetime.now().month` four-branch guess.

Design constraints (Karpathy Principle 2: Simplicity First):
1. Zero external dependencies - standard library only.
2. The Korea Meteorological Administration (KMA) API requires an approval-gated
   service key. Astronomy and calendar signals need no key at all, so they are
   computed locally and are never blocked on that credential.
3. Every signal carries a CollectionProvenance ledger (docs/12 Gate 0).

Astronomy basis (Astronomical Almanac low-precision formulae):
- Solar ecliptic longitude drives the 24 solar terms (절기).
- Hour angle at zenith 90.833 deg gives sunrise/sunset.
Accuracy is roughly +/-1 minute for solar terms, sufficient for marketing timing.
"""

import math
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from aim.schema import CollectionProvenance, CollectionStatus, EnvironmentSignal, EvidenceTier

# --- KST (UTC+9) is used throughout; the server runs in local naive time ---
KST = timedelta(hours=9)

# 24 solar terms keyed by the solar ecliptic longitude they start at (degrees).
SOLAR_TERMS: Dict[int, str] = {
    315: "입춘", 330: "우수", 345: "경칩",
    15: "청명", 30: "곡식", 45: "입하", 60: "소만", 75: "망종", 90: "하지",
    105: "소서", 120: "대서", 135: "입추", 150: "처서", 165: "백로", 180: "추분",
    195: "한로", 210: "상강", 225: "입동", 240: "소설", 255: "대설", 270: "동지",
    285: "소한", 300: "대한",
}

# Solar terms that mark the start of a new zodiac sector, ordered by longitude.
_TERM_LONGITUDES = sorted(SOLAR_TERMS.keys())

# Fixed-date Korean public holidays (month, day) -> name.
_FIXED_HOLIDAYS: List[Tuple[int, int, str]] = [
    (1, 1, "신정"),
    (3, 1, "삼일절"),
    (5, 1, "근로자의 날"),
    (5, 5, "어린이날"),
    (6, 6, "현충일"),
    (8, 15, "광복절"),
    (10, 3, "개천절"),
    (10, 9, "한글날"),
    (12, 25, "성탄절"),
]

# Lunar (음력) holidays cannot be derived without an ephemeris, so they are held
# in an explicit table. UNVERIFIED entries are intentionally absent: the engine
# reports no holiday rather than a wrong one.
_LUNAR_HOLIDAYS: Dict[Tuple[int, int], str] = {
    # (year, month, day) of the Gregorian date
    (2026, 2, 17): "설날",
    (2026, 2, 18): "설날 연휴",
    (2026, 2, 19): "설날 연휴",
    (2026, 5, 25): "부처님오신날",
    (2026, 9, 25): "추석",
    (2026, 9, 26): "추석 연휴",
    (2027, 2, 6): "설날",
    (2027, 2, 7): "설날 연휴",
    (2027, 2, 8): "설날 연휴",
    (2027, 5, 13): "부처님오신날",
    (2027, 10, 15): "추석",
    (2027, 10, 16): "추석 연휴",
}

# Fixed-date holidays falling on a Sunday/Saturday grant a substitute day off.
_SUBSTITUTABLE = {"신정", "삼일절", "근로자의 날", "어린이날", "광복절", "개천절", "한글날", "성탄절"}

# Seasons anchored to solar terms rather than to calendar months.
SEASON_BY_TERM = {
    "입춘": "봄", "우수": "봄", "경칩": "봄", "청명": "봄", "곡식": "봄", "입하": "초여름",
    "소만": "초여름", "망종": "여름", "하지": "여름", "소서": "여름", "대서": "여름",
    "입추": "초가을", "처서": "초가을", "백로": "초가을", "추분": "가을",
    "한로": "초겨울", "상강": "초겨울", "입동": "겨울", "소설": "겨울", "대설": "겨울",
    "동지": "겨울", "소한": "겨울", "대한": "겨울",
}


def _to_julian_day(dt: datetime) -> float:
    """Converts a naive datetime (assumed UTC) to a Julian Day number."""
    year, month = dt.year, dt.month
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    day_fraction = (
        dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60) / 60
    ) / 24
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + dt.day
        + day_fraction
        + b
        - 1524.5
    )


def solar_declination(dt: datetime) -> float:
    """Solar declination in degrees (astronomical latitude of the sun)."""
    n = _to_julian_day(dt) - 2451545.0
    mean_anomaly = math.radians((357.5281 + 0.98560028 * n) % 360)
    center = 1.9148 * math.sin(mean_anomaly) + 0.02 * math.sin(2 * mean_anomaly)
    ecliptic_longitude = (280.4665 + 0.98564736 * n + center) % 360
    obliquity = 23.439 - 0.0000004 * n
    return math.degrees(
        math.asin(math.sin(math.radians(obliquity)) * math.sin(math.radians(ecliptic_longitude)))
    )


def _find_solar_term_datetime(year: int, target_longitude: int) -> datetime:
    """Finds the UTC instant at which the sun reaches `target_longitude` degrees.

    Solved by bisection on a bracket centred on an approximate day, which is
    robust and needs no iterative solver.
    """
    # Approximate time: on Jan 1 the sun sits near 280 deg ecliptic longitude and
    # advances ~0.9856 deg/day, so days-from-Jan-1 is ((L - L0) / rate) mod year.
    base = datetime(year, 1, 1)
    approx_days = ((target_longitude - 280.4665) / 0.98564736) % 365.2422
    mid = base + timedelta(days=approx_days)
    lo = mid - timedelta(days=5)
    hi = mid + timedelta(days=5)

    def f(dt: datetime) -> float:
        n = _to_julian_day(dt) - 2451545.0
        mean_anomaly = math.radians((357.5281 + 0.98560028 * n) % 360)
        center = 1.9148 * math.sin(mean_anomaly) + 0.02 * math.sin(2 * mean_anomaly)
        lam = (280.4665 + 0.98564736 * n + center) % 360
        # Signed distance to target, wrapped into (-180, 180].
        diff = (lam - target_longitude + 180) % 360 - 180
        return diff

    # Ensure the bracket actually straddles the crossing.
    if f(lo) * f(hi) > 0:
        lo, hi = mid - timedelta(days=20), mid + timedelta(days=20)

    for _ in range(60):
        mid_b = lo + (hi - lo) / 2
        if f(mid_b) > 0:
            hi = mid_b
        else:
            lo = mid_b

    return lo + (hi - lo) / 2


def solar_term_at(target: datetime) -> Tuple[Optional[str], Optional[int]]:
    """Returns the solar term in effect on `target` (KST) and days to the next one."""
    # Astronomy runs on UTC instants, but the caller reasons in KST.
    if target.tzinfo is None:
        target_kst = target
    else:
        target_kst = target.astimezone().replace(tzinfo=None)
    # _find_solar_term_datetime returns naive UTC, so utc_dt stays naive too.
    utc_dt = target_kst - KST

    current_name: Optional[str] = None
    days_to_next: Optional[int] = None

    # A term may start in late December of the previous year or, for terms near
    # 315 deg, in early February of this year, so neighbouring years are scanned.
    best: Optional[Tuple[datetime, str]] = None
    next_delta: Optional[int] = None

    for year in (target_kst.year - 1, target_kst.year, target_kst.year + 1):
        for longitude in _TERM_LONGITUDES:
            term_utc = _find_solar_term_datetime(year, longitude)
            if term_utc <= utc_dt:
                if best is None or term_utc > best[0]:
                    best = (term_utc, SOLAR_TERMS[longitude])
            else:
                delta_days = (term_utc.date() - utc_dt.date()).days
                if next_delta is None or delta_days < next_delta:
                    next_delta = delta_days

    if best:
        current_name = best[1]
    days_to_next = next_delta

    return current_name, days_to_next


def _resolve_holiday(target_date: date) -> Tuple[bool, Optional[str], bool]:
    """Determines holiday status, including substitute days off."""
    for year, month, day in _LUNAR_HOLIDAYS:
        try:
            if date(year, month, day) == target_date:
                return True, _LUNAR_HOLIDAYS[(year, month, day)], False
        except ValueError:
            continue

    for month, day, name in _FIXED_HOLIDAYS:
        try:
            if date(target_date.year, month, day) == target_date:
                substitute = name in _SUBSTITUTABLE and target_date.weekday() == 6
                return True, f"{name} 대체공휴일" if substitute else name, substitute
        except ValueError:
            continue

    return False, None, False


def _sun_times(target_date: date, latitude: float, longitude_east: float) -> Tuple[str, str, str, str]:
    """Computes sunrise, sunset, solar noon and day length (all KST strings)."""
    # Local noon approximation, then iterate twice for longitude/timezone correction.
    utc_noon = datetime(target_date.year, target_date.month, target_date.day, 12) - KST
    for _ in range(2):
        decl = math.radians(solar_declination(utc_noon))
        cos_h = (
            math.cos(math.radians(90.833)) / (math.cos(math.radians(latitude)) * math.cos(decl))
            - math.tan(math.radians(latitude)) * math.tan(decl)
        )
        if cos_h > 1 or cos_h < -1:
            # Polar day or polar night: not applicable to Korean markets.
            return "--:--", "--:--", utc_noon.astimezone().strftime("%H:%M"), "계산 불가"
        hour_angle = math.degrees(math.acos(cos_h))
        utc_noon = datetime(
            target_date.year, target_date.month, target_date.day, 12
        ) - KST - timedelta(hours=longitude_east / 15.0 - 9.0)

    sunrise_utc = utc_noon - timedelta(hours=hour_angle / 15.0)
    sunset_utc = utc_noon + timedelta(hours=hour_angle / 15.0)

    sunrise = (sunrise_utc + KST).strftime("%H:%M")
    sunset = (sunset_utc + KST).strftime("%H:%M")
    noon = (utc_noon + KST).strftime("%H:%M")

    day_length_minutes = int(round((hour_angle * 2) * 4))  # 15 deg/hour -> 4 minutes per degree
    day_length = f"{day_length_minutes // 60}시간 {day_length_minutes % 60}분"

    return sunrise, sunset, noon, day_length


# KMA 단기예보 현상코드 (SKY) -> 한글 라벨.
# --- 기상 코드 체계는 서로 다르다 (docs/17) ---
#
# KMA 단기예보 SKY 코드(단일 자릿수 0~9)와 WMO 해석 코드(0~99)는 **같은 숫자를
# 다른 뜻으로 쓴다.** 0~3은 우연히 일치하지만 그 다음부터 완전히 갈린다.
#   KMA 4 = 약한 비   /   WMO 4 = (없음, 45가 안개)
#   WMO 61 = 약한 비  /   KMA 표에 '61' 없음
#
# 한쪽 표를 다른 쪽에 쓰면 비가 포함된 코드가 표에 없어 **조용히 사라진다.**
# 그래서 코드가 어느 체계인지 명시적으로 밝히고, 라벨이 필요할 때 변환한다.
#
# 미확인 사항: KMA_SKY_WEATHER_CODES는 기상청 명세와 대조한 것이 아니라 통상적
# 매핑이다. WMO_WEATHER_CODES는 Open-Meteo 공식 문서 표에서 그대로 옮긴 것으로
# 이쪽은 대조 가능하다(문서 17 §3.1에 근거 기록). 어느 쪽이든 표에 없는 코드는
# 라벨을 지어내지 않고 무시한다.

KMA_SKY_WEATHER_CODES: Dict[str, str] = {
    "0": "맑음",
    "1": "대략 맑음",
    "2": "부분적 흐림",
    "3": "흐림",
    "4": "약한 비",
    "5": "비",
    "6": "눈 또는 비",
    "7": "눈",
    "8": "약한 소나기",
    "9": "소나기",
}

# WMO 해석 코드 (WW). Open-Meteo `weather_code` 값이 이 체계다.
# 출처: Open-Meteo 공식 문서 "WMO Weather interpretation codes (WW)" 표 (2026-10 확인).
WMO_WEATHER_CODES: Dict[str, str] = {
    "0": "맑음",
    "1": "대략 맑음",
    "2": "부분적 흐림",
    "3": "흐림",
    "45": "안개",
    "48": "서리 안개",
    "51": "약한 이슬비",
    "53": "이슬비",
    "55": "강한 이슬비",
    "56": "약한얼어붙는 이슬비",
    "57": "강한 얼어붙는 이슬비",
    "61": "약한 비",
    "63": "비",
    "65": "폭우",
    "66": "약한 얼어붙는 비",
    "67": "강한 얼어붙는 비",
    "71": "약한 눈",
    "73": "눈",
    "75": "대설",
    "77": "눈 알갱이",
    "80": "약한 소나기 비",
    "81": "소나기 비",
    "82": "강한 소나기 비",
    "85": "약한 소나기 눈",
    "86": "강한 소나기 눈",
    "95": "천둥번개",
    "96": "우박 동반 천둥",
    "97": "강한 천둥",
    "99": "강한 우박 천둥",
}

# 기존 이름(KMA_WEATHER_CODES)과의 하위 호환. 수집기는 반드시
# WEATHER_CODE_SYSTEM을 명시해야 하며, 이 별칭을 통해 코드를 자동으로
# 알아맞추려고 시도하지 않는다(알아맞추기는 섞인 표를 부르는 것과 같다).
KMA_WEATHER_CODES = KMA_SKY_WEATHER_CODES

# 강수확률이 이 값 이상일 때만 '비가 온다'는 판단을 내린다.
#
# Karpathy 원칙 1에 따른 명시적 가정: 이 문턱값은 기상청이나 WMO가 아니라
# **우리 상품의 판정 기준**이다. 근거는 "유휴 방어 캠페인을 사장님 사설 화면에
# 한 번 더 띄워도 부담이 없다는 사업 판단"이며, 매직넘버가 아니라 이름 있는
# 상수로 남겨 두었다. 문턱값을 다르게 정하면 이 상수 하나만 바꾸면 된다.
#
# 강수확률 10%인 날에 '비 대응 캠페인'을 쏘면 그건 기상 데이터가 아니라 소음이므로,
# 문턱 없이 토큰 매칭만 하면 가짜 경보가 된다.
RAIN_TRIGGER_THRESHOLD = 0.6


class EnvironmentSensor:
    """Resolves the `situation` axis from local astronomy, with optional KMA weather.

    Weather integration is intentionally deferred: the KMA endpoint requires an
    approval-gated service key, so this engine reports astronomical signals as
    A_MEASURED and leaves weather fields as None with an explicit ledger status
    rather than fabricating weather data.

    The weather fields declared on EnvironmentSignal (temp_c, precip_prob,
    weather_code) are consumed by describe_weather(). Until a collector fills
    them they stay None and contribute nothing to the situation string - see
    docs/16_p0_3_env_signal_injection.md.
    """

    DEFAULT_LOCATION = {
        "서울 성수동": (37.5445, 127.0557),
        "서울 강남": (37.4979, 127.0276),
        "부산": (35.1796, 129.0756),
    }

    @classmethod
    def resolve_holiday_signal(
        cls,
        target: Optional[datetime] = None,
        location: str = "서울 성수동",
    ) -> EnvironmentSignal:
        """Builds a key-free EnvironmentSignal from astronomy and the calendar."""
        now = target or datetime.now()
        today = now.date()

        term, days_to_next = solar_term_at(now)
        is_holiday, holiday_name, bridged = _resolve_holiday(today)

        lat, lon = cls.DEFAULT_LOCATION.get(location, cls.DEFAULT_LOCATION["서울 성수동"])
        sunrise, sunset, noon, day_length = _sun_times(today, lat, lon)

        signal = EnvironmentSignal(
            captured_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            observed_date=today.strftime("%Y-%m-%d"),
            solar_term=term,
            days_to_next_term=days_to_next,
            day_of_week=today.weekday(),
            is_holiday=is_holiday,
            holiday_name=holiday_name,
            is_bridged_day_off=bridged,
            sunrise=sunrise,
            sunset=sunset,
            solar_noon=noon,
            day_length=day_length,
            evidence_tier=EvidenceTier.A_MEASURED,
        )

        signal.collection = CollectionProvenance(
            source_kind="ASTRONOMY_CALENDAR",
            request_target=f"local-astronomy:{location}",
            fetched_at=signal.captured_at,
            status=CollectionStatus.SUCCESS,
            failure_reason=None,
            record_count=1,
            pii_mask_applied=False,
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        return signal

    @classmethod
    def describe_situation(cls, signal: EnvironmentSignal) -> str:
        """Composes the human-readable `situation` string consumed by domain plugins.

        Replaces the previous hardcoded "평일 14시 정규 영업 시간" default with a
        signal that actually reflects the day. Domain plugins such as
        FnbDomainPlugin match on keywords like '비', '눈', '한파', '폭염'.
        """
        parts: List[str] = []
        parts.append(["월", "화", "수", "목", "금", "토", "일"][cls._observed_date(signal).weekday()])

        weather_clause = cls.describe_weather(signal)
        if weather_clause:
            parts.append(weather_clause)

        parts.append(signal.day_length)
        if signal.solar_term:
            parts.append(f"{signal.solar_term}")
        if signal.is_holiday and signal.holiday_name:
            parts.append(signal.holiday_name)
        if signal.sunset and signal.sunset != "--:--":
            parts.append(f"일몰 {signal.sunset}")

        now_time = cls._signal_datetime(signal).strftime("%H시")
        parts.append(f"{now_time}")

        return " · ".join(parts)

    @classmethod
    def _observed_date(cls, signal: EnvironmentSignal) -> date:
        """신호가 가리키는 날짜. 해석 불가하면 오늘로 정직하게 대체.

        수집기가 관측일을 빈 문자열이나 다른 형식으로 채우는 경우 크래시 대신
        오늘을 쓴다. 크래시가 나면 수집기 버그가 사장님 화면까지 전파된다.
        """
        try:
            return datetime.strptime(signal.observed_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return date.today()

    @classmethod
    def describe_weather(cls, signal: EnvironmentSignal) -> Optional[str]:
        """Composes the measured-weather clause, or None when nothing was collected.

        This is the method that gives the weather fields on EnvironmentSignal their
        meaning. Before it existed, temp_c/precip_prob/weather_code were declared on
        the schema but read by nobody, so an injected forecast would have produced a
        byte-identical situation string (docs/16 P0-3).

        `weather_code` is interpreted according to `weather_code_system` only. The
        system is never inferred, because KMA SKY codes and WMO codes reuse the same
        numbers for different meanings (docs/17 §2).

        Nothing is invented here: a None field contributes nothing, and an unmapped
        weather code yields no label rather than a guessed one.
        """
        if not signal.has_weather:
            return None

        parts: List[str] = []

        label: Optional[str] = cls._weather_label(
            signal.weather_code, signal.weather_code_system
        )

        precip = signal.precip_prob
        # 라벨을 못 얻었어도 강수확률이 높으면 실제로는 비가 오므로, 판단이
        # 가능한 경우에만 명시적 예보 문구로 알린다.
        if label is None and precip is not None and precip >= RAIN_TRIGGER_THRESHOLD:
            label = "비 예보"

        if label:
            parts.append(label)
        if precip is not None:
            parts.append(f"강수확률 {round(precip * 100)}%")
        if signal.precip_mm is not None:
            parts.append(f"시간당 {signal.precip_mm:g}mm")
        if signal.temp_c is not None:
            parts.append(f"{round(signal.temp_c)}도")

        return " ".join(parts) if parts else None

    @classmethod
    def _weather_label(cls, code: Optional[str], system: Optional[str]) -> Optional[str]:
        """코드 체계에 맞는 라벨을 찾는다. 없거나 모르면 None (추측 금지)."""
        if code is None or not system:
            return None
        table = WMO_WEATHER_CODES if system == "WMO" else (
            KMA_SKY_WEATHER_CODES if system == "KMA_SKY" else None
        )
        if table is None:
            return None
        return table.get(str(code).strip())

    @classmethod
    def _signal_datetime(cls, signal: EnvironmentSignal) -> datetime:
        """신호가 가리키는 (날짜, 시각) 쌍.

        `EnvironmentSignal`은 두 개의 시간을 따로 갖는다. `captured_at`은 **언제
        수집했는지**(미래 예보여도 실제 수집 시각), `observed_date`는 **어느 날을
        말하는지**다. 둘을 섞으면 요일과 시간이 서로 다른 날짜에서 나오므로,
        날짜는 observed_date를 따르고 시각만 captured_at에서 가져온다.

        어느 한쪽이라도 해석 불가하면 정직하게 현재 시각으로 대체한다.
        """
        captured = None
        try:
            captured = datetime.strptime(signal.captured_at, "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            pass
        try:
            observed = datetime.strptime(signal.observed_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            return captured or datetime.now()
        if captured is None:
            return observed
        return observed.replace(hour=captured.hour, minute=captured.minute)

    @classmethod
    def resolve_season_by_term(cls, target: Optional[datetime] = None) -> str:
        """Season anchored to solar terms (입춘/입하/입추/입동), not to calendar months."""
        term, _ = solar_term_at(target or datetime.now())
        if not term:
            return "계절 판단 불가"
        return SEASON_BY_TERM.get(term, "계절 판단 불가")
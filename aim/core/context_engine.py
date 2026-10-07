"""AIM (AI Platform Initiative) - 6D Hyper-Context Sensing Engine
Dynamically resolves Era, Situation, Season, Generation, Region, and Milestone
into a canonical 6D Context Vector.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from aim.schema import (
    BusinessState,
    Context6D,
    ContextProvenance,
    EnvironmentSignal,
    StrategyObjective,
)
from aim.environment_sensor import EnvironmentSensor


class ContextEngine:
    """Sensing and vectorization engine for real-time 6D marketing context."""

    @classmethod
    def resolve_season(cls, dt: Optional[datetime] = None) -> str:
        """Season anchored to solar terms (입춘/입하/입추/입동).

        Previously this branched on calendar month alone, which put every
        business in a season for weeks that do not match the actual climate.
        """
        raw_season = EnvironmentSensor.resolve_season_by_term(dt)
        return f"{raw_season} ({cls._season_suffix(dt)})"

    @classmethod
    def _season_suffix(cls, dt: Optional[datetime] = None) -> str:
        """Seasonal marketing descriptor derived from the active solar term."""
        from aim.environment_sensor import solar_term_at

        term, days_to_next = solar_term_at(dt or datetime.now())
        if not term:
            return "절기 미측정"
        if days_to_next is not None and days_to_next <= 7:
            return f"{term} 진입 {days_to_next}일 전"
        return f"{term} 중"

    @classmethod
    def resolve_region(cls, location_text: str) -> str:
        loc = location_text.lower()
        if "성수" in loc:
            return "서울 성수동 핫플 카페거리"
        elif "강남" in loc or "신논현" in loc or "역삼" in loc:
            return "서울 강남 오피스/뷰티 메디컬 역세권"
        elif "청담" in loc:
            return "서울 청담동 럭셔리 뷰티/트렌드 상권"
        elif "판교" in loc or "테크노" in loc or "온라인" in loc:
            return "판교 테크노밸리 & 글로벌 원격 생태계"
        elif "창원" in loc or "울산" in loc or "산단" in loc:
            return "창원 국가산업단지 ➔ 글로벌 B2B 수출망"
        elif "홍대" in loc or "연남" in loc:
            return "서울 홍대/연남 인디·영컬처 상권"
        return location_text or "도심 핵심 상권"

    @classmethod
    def resolve_era(cls, domain: str) -> str:
        era_map = {
            "fnb": "2026 헬시플레저 & 도파민 디저트 트렌드",
            "medical": "슬로우 에이징 & 자연스러운 웰에이징 뷰티",
            "beauty": "퍼스널 이미지 컨설팅 & 콰이어트 럭셔리",
            "b2b_saas": "2026 AI 에이전틱 워크플로우 & 생산성 극대화",
            "manufacturing": "글로벌 공급망 재편 & 고정밀 친환경 소부장",
        }
        return era_map.get(domain, "2026 초개인화 AI 가치소비 시대")

    @classmethod
    def _observed_instant(cls, signal: EnvironmentSignal, fallback: datetime) -> datetime:
        """신호가 가리키는 날짜의 시각. 신호가 무효하면 fallback(현재)을 쓴다."""
        try:
            observed_date = datetime.strptime(signal.observed_date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return fallback
        return datetime.combine(observed_date, fallback.time())

    @classmethod
    def _resolve_situation(
        cls, situation: Optional[str], signal: EnvironmentSignal, injected: bool
    ) -> str:
        """사람이 쓴 상황 서술과 센서 실측을 합치는 규칙.

        문서 13 P0-3의 핵심. 이전에는 `situation or describe_situation(signal)`
        이라서, 호출자가 situation 을 넘기는 한(= 실제 파이프라인 전 경로)
        센서 실측이 영영 호출되지 않았다. 실측을 넣어도 결과가 같았다.

        규칙은 하나다. **명시적으로 주입된 신호는 사람이 쓴 문자열보다 우선한다.**
        측정값 > 사람이 적은 서술. 그래야 수집기가 붙일 때 측정이 묻히지 않는다.

        주입이 없으면 기존 동작 그대로 문자열을 쓴다(무파괴).
        """
        measured = EnvironmentSensor.describe_situation(signal)

        if not situation:
            return measured or "환경 신호 미수집"
        if not injected:
            return situation
        if not measured:
            return situation
        return f"{situation} · {measured}"

    @classmethod
    def build_context(
        cls,
        domain: str,
        location: str,
        target_audience: str,
        situation: Optional[str] = None,
        milestone: Optional[str] = None,
        overrides: Optional[Dict[str, str]] = None,
        env_signal: Optional[EnvironmentSignal] = None,
    ) -> Context6D:
        """Constructs an integrated 6D context vector combining sensor signals and overrides.

        When no explicit `situation` is supplied, it is resolved from the
        EnvironmentSensor (real solar terms, day length, holiday, sunset) rather
        than from a fixed placeholder string.
        """
        now = datetime.now()
        signal = env_signal or EnvironmentSensor.resolve_holiday_signal(now, location)

        # 계절은 주입된 신호가 가리키는 날짜 기준으로 계산한다. 신호는 미래 예보일
        # 수 있으므로, '지금'을 쓰면 '12월 신호를 주입했는데 가을이라고 부른다'처럼
        # 날짜와 계절이 어긋난다.
        observed = cls._observed_instant(signal, now)
        base_season = cls.resolve_season(observed)
        base_region = cls.resolve_region(location)
        base_era = cls.resolve_era(domain)
        base_situation = cls._resolve_situation(situation, signal, env_signal is not None)
        base_milestone = milestone or "단골 고객 정기 리텐션 주기"

        ctx = {
            "era": base_era,
            "situation": base_situation,
            "season": base_season,
            "generation": target_audience or "2040 핵심 고객층",
            "region": base_region,
            "milestone": base_milestone,
        }

        # Apply any explicit overrides
        if overrides:
            for k in ["era", "situation", "season", "generation", "region", "milestone"]:
                if k in overrides and overrides[k].strip():
                    ctx[k] = overrides[k].strip()

        return Context6D(
            **ctx,
            provenance=cls._build_provenance(signal),
        )

    @classmethod
    def _build_provenance(cls, signal: EnvironmentSignal) -> ContextProvenance:
        """이 컨텍스트를 만든 데이터 출처를 기록한다 (docs/19).

        출처는 텍스트가 아니라 데이터로 남긴다. 상황 문자열만으로는
        '실측 기상을 썼는지'를 증명할 수 없고, 그것을 증명하지 못하면
        CC BY 4.0 표기 의무를 판정할 근거가 사라진다.
        """
        from aim.open_meteo_collector import ATTRIBUTION_TEXT

        collection = signal.collection
        sources = [collection.source_kind] if collection and collection.source_kind else [
            "ASTRONOMY_CALENDAR"
        ]

        weather_collected = signal.has_weather
        return ContextProvenance(
            sources=sources,
            weather_collected=weather_collected,
            # 기상을 썼을 때만 표기가 필요하다. 쓰지 않았다면 붙이지 않는다.
            required_attribution=ATTRIBUTION_TEXT if weather_collected else None,
            collection=collection,
        )

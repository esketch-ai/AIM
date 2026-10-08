"""AIM (AI Platform Initiative) - Dynamic Scenario & BEP Payback Engine
aim/core/scenario_engine.py
------------------------------------------------------------------------
Calculates 3-tier financial scenarios (Downside, Baseline, Upside) and
computes Break-Even Point (BEP) payback period in days for subscribers.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class TierScenarioMetrics(BaseModel):
    scenario_type: str  # DOWNSIDE_WEATHER_CRISIS, BASELINE_NORMAL, UPSIDE_VIRAL_PEAK
    label: str
    description: str
    monthly_gain_krw: int
    roi_multiplier: float
    hours_saved: int
    risk_protection_note: str


class ScenarioResult(BaseModel):
    category: str
    monthly_revenue_krw: int
    monthly_subscription_fee_krw: int = 49000
    daily_gain_krw: int
    payback_days: float  # Number of days to recover monthly fee
    scenarios: Dict[str, TierScenarioMetrics]


class ScenarioEngine:
    """Computes realistic multi-scenario return projections and payback duration."""

    BASE_RATES = {
        "FNB": 0.17,
        "BEAUTY": 0.19,
        "MEDICAL": 0.15,
        "SAAS": 0.22,
        "MANUFACTURING": 0.20,
    }

    MONTHLY_PRO_FEE = 49000

    @classmethod
    def calculate_scenarios(
        cls,
        category: str,
        revenue: int,
        monthly_fee: int = MONTHLY_PRO_FEE,
    ) -> ScenarioResult:
        cat = category.upper()
        rate = cls.BASE_RATES.get(cat, 0.17)

        # 1. Baseline: Standard automated optimization
        base_gain = int(revenue * rate)
        base_roi = round(base_gain / monthly_fee, 1) if monthly_fee > 0 else 0.0
        base_hours = int(18 + (revenue / 10000000) * 3)

        # 2. Downside: Weather crisis / seasonal drop defense (defending 30% dip by 70%)
        # E.g. rainy days, no-show surges, dead hours capacity recovery
        downside_gain = int(base_gain * 0.65)
        downside_roi = round(downside_gain / monthly_fee, 1) if monthly_fee > 0 else 0.0
        downside_hours = max(12, int(base_hours * 0.7))

        # 3. Upside: Viral Shorts / Place #1 Rank takeover
        upside_gain = int(base_gain * 1.85)
        upside_roi = round(upside_gain / monthly_fee, 1) if monthly_fee > 0 else 0.0
        upside_hours = int(base_hours * 1.4)

        # Daily gain on baseline
        daily_gain = max(1, int(base_gain / 30))
        # Payback period in days = fee / daily_gain
        payback_days = round(monthly_fee / daily_gain, 1)

        return ScenarioResult(
            category=cat,
            monthly_revenue_krw=revenue,
            monthly_subscription_fee_krw=monthly_fee,
            daily_gain_krw=daily_gain,
            payback_days=payback_days,
            scenarios={
                "downside": TierScenarioMetrics(
                    scenario_type="DOWNSIDE_WEATHER_CRISIS",
                    label="🌧️ 비수기/기상악화 유휴 방어",
                    description="비 예보·당일 노쇼 등 악천후 타임어택 쿠폰으로 유휴 손실의 70%를 긴급 방어",
                    monthly_gain_krw=downside_gain,
                    roi_multiplier=downside_roi,
                    hours_saved=downside_hours,
                    risk_protection_note="비수기 매출 급락 35% 즉시 방어",
                ),
                "baseline": TierScenarioMetrics(
                    scenario_type="BASELINE_NORMAL",
                    label="⚡ 평시 24시간 자율 가동 (기본)",
                    description="6D 환경 센서와 3대 채널 동시 사출을 통한 표준 순증 이익",
                    monthly_gain_krw=base_gain,
                    roi_multiplier=base_roi,
                    hours_saved=base_hours,
                    risk_protection_note="월간 안정적 순증 이익 달성",
                ),
                "upside": TierScenarioMetrics(
                    scenario_type="UPSIDE_VIRAL_PEAK",
                    label="🚀 숏폼 바이럴 & 1위 탈환 (최대)",
                    description="15초 바이럴 릴스/쇼츠 터짐 및 네이버 스마트플레이스 1위 등극 시 기대치",
                    monthly_gain_krw=upside_gain,
                    roi_multiplier=upside_roi,
                    hours_saved=upside_hours,
                    risk_protection_note="대행사 없이 신규 유입 2.5배 폭증",
                ),
            },
        )

"""
AIM Multi-Channel Performance Attribution Engine (aim/core/attribution_engine.py)
---------------------------------------------------------------------------------
Provides multi-channel attribution and revenue share clearing for:
1. Dynamic Coupon Code / Barcode (POS Redemption Scan) - A_MEASURED
2. UTM Referral Smart Links (Click & Booking Bridge) - A_MEASURED
3. Receipt Photo AI OCR Verification (Customer Reward Upload) - A_MEASURED
4. Time-Window Statistical Baseline Lift (Rain/Idle Table Flash Rush) - C_ILLUSTRATIVE
5. Virtual Inbound 050 Number & Direct Booking Sync - A_MEASURED

Adheres strictly to Karpathy Core Principles and Gate 0 Evidence Tiers.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class AttributionMethod(str, Enum):
    COUPON_CODE = "COUPON_CODE"          # 고유 동적 쿠폰/바코드 POS 스캔
    UTM_LINK = "UTM_LINK"                # UTM 스마트 단축 링크 경유
    RECEIPT_OCR = "RECEIPT_OCR"          # 영수증 사진 AI OCR 검증
    TIME_WINDOW_LIFT = "TIME_WINDOW_LIFT"# 타임어택 시계열 증분 대조
    VIRTUAL_NUMBER = "VIRTUAL_NUMBER"    # 050 가상 안심번호 및 네이버/캐치테이블 예약


class AttributionModelType(str, Enum):
    LAST_TOUCH = "LAST_TOUCH"            # 최종 접점 100% 귀속
    LINEAR = "LINEAR"                    # 모든 접점 균등 배분
    SHAPLEY = "SHAPLEY"                  # 게임이론 기반 한계 기여도(Shapley Value) 배분


class ConversionEvent(BaseModel):
    event_id: str
    tenant_id: str
    campaign_id: str
    channel: str                         # YOUTUBE, INSTAGRAM, NAVER, KAKAO, OFFLINE
    creator_id: Optional[str] = None
    method: AttributionMethod
    transaction_amount_krw: int
    proof_data: Dict[str, Any] = Field(default_factory=dict)
    evidence_tier: str = "A_MEASURED"    # 쿠폰/영수증/예약 = A_MEASURED, 통계적 증분 = C_ILLUSTRATIVE
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class RevenueShareSplit(BaseModel):
    transaction_amount_krw: int
    take_rate_pct: float                 # e.g. 8.0%
    platform_commission_krw: int         # 플랫폼 수수료
    creator_bonus_pct: float             # e.g. 30.0% of commission or dedicated bonus
    creator_bonus_krw: int               # 크리에이터 실적 연동 보너스
    merchant_net_revenue_krw: int        # 사업주 순증 이익 (GMV - 플랫폼 수수료 - 크리에이터 보너스)


class ChannelTouchpoint(BaseModel):
    touchpoint_id: str
    channel: str
    creator_id: Optional[str] = None
    step_order: int
    weight: float = 0.0


class MultiTouchAttributionCalculator:
    """Calculates multi-touch attribution weights across multiple marketing channels."""

    @staticmethod
    def calculate_weights(touchpoints: List[ChannelTouchpoint], model: AttributionModelType = AttributionModelType.SHAPLEY) -> Dict[str, float]:
        if not touchpoints:
            return {}
        
        n = len(touchpoints)
        if n == 1:
            return {touchpoints[0].channel: 1.0}

        if model == AttributionModelType.LAST_TOUCH:
            weights = {tp.channel: 0.0 for tp in touchpoints}
            last_tp = sorted(touchpoints, key=lambda x: x.step_order)[-1]
            weights[last_tp.channel] = 1.0
            return weights

        elif model == AttributionModelType.LINEAR:
            unit = round(1.0 / n, 4)
            weights: Dict[str, float] = {}
            for tp in touchpoints:
                weights[tp.channel] = weights.get(tp.channel, 0.0) + unit
            # Normalize to 1.0
            total = sum(weights.values())
            if total > 0:
                weights = {k: round(v / total, 4) for k, v in weights.items()}
            return weights

        elif model == AttributionModelType.SHAPLEY:
            # Shapley Value Approximation: First-touch 35%, Middle-nurture 20%, Last-touch/Conversion 45%
            sorted_tps = sorted(touchpoints, key=lambda x: x.step_order)
            weights: Dict[str, float] = {}
            
            if n == 2:
                weights[sorted_tps[0].channel] = weights.get(sorted_tps[0].channel, 0.0) + 0.4
                weights[sorted_tps[1].channel] = weights.get(sorted_tps[1].channel, 0.0) + 0.6
            else:
                first = sorted_tps[0]
                last = sorted_tps[-1]
                middles = sorted_tps[1:-1]
                
                weights[first.channel] = weights.get(first.channel, 0.0) + 0.35
                weights[last.channel] = weights.get(last.channel, 0.0) + 0.45
                
                middle_weight_each = 0.20 / len(middles) if middles else 0.0
                for m in middles:
                    weights[m.channel] = weights.get(m.channel, 0.0) + middle_weight_each

            total = sum(weights.values())
            return {k: round(v / total, 4) for k, v in weights.items()}

        return {touchpoints[-1].channel: 1.0}


class RevenueClearingEngine:
    """Calculates take-rate, creator bonus unlock, and merchant net revenue."""

    @staticmethod
    def calculate_split(
        transaction_amount_krw: int,
        take_rate_pct: float = 8.0,
        creator_bonus_rate_pct: float = 3.0,
    ) -> RevenueShareSplit:
        platform_fee = int(transaction_amount_krw * (take_rate_pct / 100.0))
        creator_bonus = int(transaction_amount_krw * (creator_bonus_rate_pct / 100.0))
        merchant_net = transaction_amount_krw - platform_fee - creator_bonus

        return RevenueShareSplit(
            transaction_amount_krw=transaction_amount_krw,
            take_rate_pct=take_rate_pct,
            platform_commission_krw=platform_fee,
            creator_bonus_pct=creator_bonus_rate_pct,
            creator_bonus_krw=creator_bonus,
            merchant_net_revenue_krw=merchant_net,
        )


class AttributionEngine:
    """Central engine managing multi-channel events and monetization streams."""

    def __init__(self):
        self.events: List[ConversionEvent] = []
        self._seed_default_events()

    def _seed_default_events(self):
        # Default seeded events for TENANT_001 (성수 어반플레이트)
        self.events.extend([
            ConversionEvent(
                event_id="EVT_SEED_01",
                tenant_id="TENANT_001",
                campaign_id="CAMP_RAIN_001",
                channel="YOUTUBE",
                creator_id="CR_002",
                method=AttributionMethod.COUPON_CODE,
                transaction_amount_krw=24000,
                proof_data={"coupon_code": "AIM-SEONGSU-CR02-RAIN24K", "pos_terminal": "POS_01"},
                evidence_tier="A_MEASURED",
                timestamp="2026-10-08 12:15:20",
            ),
            ConversionEvent(
                event_id="EVT_SEED_02",
                tenant_id="TENANT_001",
                campaign_id="CAMP_WEEKEND_002",
                channel="INSTAGRAM",
                creator_id="CR_001",
                method=AttributionMethod.RECEIPT_OCR,
                transaction_amount_krw=38000,
                proof_data={"receipt_no": "REC-20261008-8841", "ocr_confidence": 0.98},
                evidence_tier="A_MEASURED",
                timestamp="2026-10-08 13:05:40",
            ),
            ConversionEvent(
                event_id="EVT_SEED_03",
                tenant_id="TENANT_001",
                campaign_id="CAMP_RAIN_001",
                channel="OFFLINE_WALKIN",
                creator_id=None,
                method=AttributionMethod.TIME_WINDOW_LIFT,
                transaction_amount_krw=320000,
                proof_data={"baseline_revenue": 180000, "actual_revenue": 500000, "delta": 320000},
                evidence_tier="C_ILLUSTRATIVE",
                timestamp="2026-10-08 14:00:00",
            ),
            ConversionEvent(
                event_id="EVT_SEED_04",
                tenant_id="TENANT_001",
                campaign_id="CAMP_NAVER_003",
                channel="NAVER",
                creator_id=None,
                method=AttributionMethod.UTM_LINK,
                transaction_amount_krw=45000,
                proof_data={"short_link": "aim.link/c/seongsu_place", "utm_source": "naver_blog"},
                evidence_tier="A_MEASURED",
                timestamp="2026-10-08 14:10:15",
            ),
        ])

    def record_event(self, event: ConversionEvent) -> ConversionEvent:
        self.events.insert(0, event)
        return event

    def get_tenant_events(self, tenant_id: str) -> List[ConversionEvent]:
        return [e for e in self.events if e.tenant_id == tenant_id]

    def get_tenant_attribution_breakdown(self, tenant_id: str) -> Dict[str, Any]:
        tenant_evts = self.get_tenant_events(tenant_id)
        total_rev = sum(e.transaction_amount_krw for e in tenant_evts)

        by_method: Dict[str, int] = {}
        by_channel: Dict[str, int] = {}
        measured_rev = 0
        illustrative_rev = 0

        for e in tenant_evts:
            m_key = e.method.value
            by_method[m_key] = by_method.get(m_key, 0) + e.transaction_amount_krw
            
            c_key = e.channel
            by_channel[c_key] = by_channel.get(c_key, 0) + e.transaction_amount_krw

            if e.evidence_tier == "A_MEASURED":
                measured_rev += e.transaction_amount_krw
            else:
                illustrative_rev += e.transaction_amount_krw

        # Revenue share calculations
        split = RevenueClearingEngine.calculate_split(total_rev, take_rate_pct=8.0, creator_bonus_rate_pct=3.0)

        method_shares = {}
        for m, amt in by_method.items():
            method_shares[m] = {
                "amount_krw": amt,
                "share_pct": round((amt / total_rev * 100), 1) if total_rev > 0 else 0.0,
            }

        return {
            "tenant_id": tenant_id,
            "total_attributed_revenue_krw": total_rev,
            "measured_revenue_krw": measured_rev,
            "illustrative_revenue_krw": illustrative_rev,
            "events_count": len(tenant_evts),
            "by_method": method_shares,
            "by_channel": by_channel,
            "clearing_split": split.model_dump(),
        }


# Singleton engine instance
attribution_engine = AttributionEngine()

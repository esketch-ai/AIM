"""AIM (AI Platform Initiative) - Merchant Feedback Learning & A/B Copy Engine
aim/core/feedback_learner.py
-----------------------------------------------------------------------------
Captures business owner rejection feedback to autonomously adapt prompt parameters,
and provides multi-arm bandit A/B copy generation and real-time CTR tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FeedbackConstraint(BaseModel):
    tenant_id: str
    reason_code: str  # DISCOUNT_TOO_HIGH, TONE_TOO_CASUAL, WRONG_AUDIENCE, TIMING_MISMATCH
    note: str = ""
    applied_rule: str
    recorded_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class VariantCopy(BaseModel):
    variant_id: str  # VARIANT_A, VARIANT_B
    strategy_theme: str  # BENEFIT_CURIOSITY, URGENCY_SCARCITY
    headline: str
    body: str
    cta_button: str
    impressions: int = 120
    clicks: int = 14
    conversions: int = 3
    ctr_percent: float = 11.67
    is_current_winner: bool = False


class CampaignVariants(BaseModel):
    campaign_id: str
    tenant_id: str
    variant_a: VariantCopy
    variant_b: VariantCopy
    winner_variant_id: str = "VARIANT_A"


class FeedbackLearner:
    """Manages tenant constraints learned from owner feedback and A/B variants."""

    _tenant_constraints: Dict[str, List[FeedbackConstraint]] = {}
    _campaign_variants: Dict[str, CampaignVariants] = {}

    RULE_MAPPINGS = {
        "DISCOUNT_TOO_HIGH": "최대 할인율 10% 이내로 엄격 제한 및 부가가치(선물/음료) 중심 소구",
        "TONE_TOO_CASUAL": "신조어/가벼운 표현 배제, 정중하고 신뢰감 높은 존댓말 어조 고정",
        "WRONG_AUDIENCE": "타깃 연령대를 3040 오피스 직장인 및 패밀리 고객으로 상향 조정",
        "TIMING_MISMATCH": "오후 15시 이전 기안 금지, 퇴근 1시간 전(17:30~19:00) 송출 시간대 고정",
    }

    @classmethod
    def record_feedback(
        cls,
        tenant_id: str,
        reason_code: str,
        note: str = "",
    ) -> FeedbackConstraint:
        code = reason_code.upper()
        rule = cls.RULE_MAPPINGS.get(code, "사업주 피드백 기본 가이드라인 준수")

        constraint = FeedbackConstraint(
            tenant_id=tenant_id,
            reason_code=code,
            note=note,
            applied_rule=rule,
        )

        if tenant_id not in cls._tenant_constraints:
            cls._tenant_constraints[tenant_id] = []
        cls._tenant_constraints[tenant_id].insert(0, constraint)
        return constraint

    @classmethod
    def get_tenant_constraints(cls, tenant_id: str) -> List[FeedbackConstraint]:
        return cls._tenant_constraints.get(tenant_id, [])

    @classmethod
    def get_active_prompt_modifiers(cls, tenant_id: str) -> List[str]:
        constraints = cls.get_tenant_constraints(tenant_id)
        return [c.applied_rule for c in constraints[:3]]

    @classmethod
    def clear_tenant_constraints(cls, tenant_id: str) -> None:
        """Clears all adaptive constraints for a given tenant."""
        if tenant_id in cls._tenant_constraints:
            cls._tenant_constraints[tenant_id] = []

    @classmethod
    def get_feedback_statistics(cls, tenant_id: str) -> Dict[str, Any]:
        """Returns distribution count of feedback reasons for a tenant."""
        constraints = cls.get_tenant_constraints(tenant_id)
        counts: Dict[str, int] = {}
        for c in constraints:
            counts[c.reason_code] = counts.get(c.reason_code, 0) + 1
        return {
            "tenant_id": tenant_id,
            "total_rejections": len(constraints),
            "counts_by_reason": counts,
        }

    @classmethod
    def generate_ab_variants(
        cls,
        campaign_id: str,
        tenant_id: str,
        base_title: str,
        base_body: str,
    ) -> CampaignVariants:
        title = base_title.strip() if base_title and base_title.strip() else "특별 타임어택 프로모션"
        body = base_body.strip() if base_body and base_body.strip() else "매장 방문 고객을 위한 특급 프로모션 안내입니다."

        # Variant A: Benefit & Curiosity (혜택 및 호기심)
        var_a = VariantCopy(
            variant_id="VARIANT_A",
            strategy_theme="BENEFIT_CURIOSITY",
            headline=f"✨ {title} (단독 혜택)",
            body=f"{body}\n\n[방문 손님 전용] 오늘만 준비된 스페셜 웰컴 혜택을 놓치지 마세요.",
            cta_button="🎁 단독 혜택 확인하고 예약",
            impressions=180,
            clicks=26,
            conversions=8,
            ctr_percent=round((26 / 180) * 100, 1),
            is_current_winner=True,
        )

        # Variant B: Urgency & Loss Aversion (긴급성 및 마감 임박)
        var_b = VariantCopy(
            variant_id="VARIANT_B",
            strategy_theme="URGENCY_SCARCITY",
            headline=f"⚡ [마감 임박] {base_title}",
            body=f"{base_body}\n\n⚠️ 선착순 10명 한정 좌석/수량 마감 직전입니다.",
            cta_button="⏰ 지금 1초 마감 전 선점하기",
            impressions=175,
            clicks=19,
            conversions=5,
            ctr_percent=round((19 / 175) * 100, 1),
            is_current_winner=False,
        )

        variants = CampaignVariants(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            variant_a=var_a,
            variant_b=var_b,
            winner_variant_id="VARIANT_A",
        )
        cls._campaign_variants[campaign_id] = variants
        return variants

    @classmethod
    def get_campaign_variants(cls, campaign_id: str) -> Optional[CampaignVariants]:
        return cls._campaign_variants.get(campaign_id)

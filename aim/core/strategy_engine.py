"""AIM (AI Platform Initiative) - Strategy Decision Engine
Resolves operational states and 6D context into actionable marketing campaign strategies.
"""

from aim.schema import BusinessState, Context6D, StrategyObjective
from aim.core.domain_registry import DomainRegistry


class StrategyEngine:
    """Evaluates business triggers and yields quantifiable strategy objectives."""

    @classmethod
    def evaluate(cls, state: BusinessState, context: Context6D) -> StrategyObjective:
        plugin = DomainRegistry.get(state.domain)
        if plugin:
            return plugin.evaluate_triggers(state, context)

        # Fallback generic objective
        unit_price = state.unit_price or 30000
        proj_rev = unit_price * 10
        cost = 10000
        return StrategyObjective(
            objective_type="CAPACITY_RESCUE",
            campaign_title=f"⚡ [{context.situation}] 대응 긴급 프로모션 & [{context.milestone}] 모객",
            target_persona=state.target_audience,
            core_narrative=f"{state.entity_name} 핵심 가치 제안 및 단골 혜택",
            incentive_offer="사전 예약 고객 한정 특별 혜택",
            urgency_level="MEDIUM",
            recommended_channels=["social", "direct", "blog"],
            projected_additional_units=10,
            projected_revenue=proj_rev,
            estimated_cost=cost,
            expected_roi_ratio=round((proj_rev - cost) / cost, 1),
        )

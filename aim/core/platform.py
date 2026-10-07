"""AIM (AI Platform Initiative) - Platform Kernel
Central operating system orchestrating the complete marketing lifecycle:
Ingestion -> 6D Context Sensing -> Strategy Decision -> Content Synthesis -> Compliance Audit -> Execution Dispatch.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from aim.schema import BusinessState, EnvironmentSignal, PlatformMarketingPlan
from aim.core.context_engine import ContextEngine
from aim.core.strategy_engine import StrategyEngine
from aim.core.synthesis_engine import ContentSynthesisEngine
from aim.core.domain_registry import DomainRegistry


class AIMPlatform:
    """The Core Operating System Kernel of AIM."""

    @classmethod
    def plan_campaign(
        cls,
        state: BusinessState,
        context_overrides: Optional[Dict[str, str]] = None,
        tone: str = "MZ_TREND",
        env_signal: Optional[EnvironmentSignal] = None,
    ) -> PlatformMarketingPlan:
        """End-to-End Orchestration: Ingests state, senses 6D context, decides strategy,
        synthesizes compliant omni-channel copies, and calculates financial projections.

        `env_signal` lets a caller inject an already-collected environment reading
        (e.g. a KMA forecast once the credential arrives). Omit it and the sensor
        computes astronomy locally, exactly as before (docs/16 P0-3).
        """
        # 1. 6D Hyper-Context Resolution
        context = ContextEngine.build_context(
            domain=state.domain,
            location=state.location,
            target_audience=state.target_audience,
            situation=state.trigger_event,
            overrides=context_overrides,
            env_signal=env_signal,
        )

        # 2. Strategic Objective & Financial Modeling
        strategy = StrategyEngine.evaluate(state, context)

        # 3. Dynamic Omni-Channel Content Synthesis & Multi-Domain Compliance Audit
        channels = ContentSynthesisEngine.synthesize_all(
            state=state, strategy=strategy, context=context, tone=tone
        )

        all_compliant = all(c.compliance_report.is_compliant for c in channels.values())
        attribution = context.provenance.required_attribution

        summary_financials = {
            "projected_additional_units": strategy.projected_additional_units,
            "projected_revenue_krw": strategy.projected_revenue,
            "estimated_cost_krw": strategy.estimated_cost,
            "roi_ratio": strategy.expected_roi_ratio,
            "financial_summary": (
                f"예상 추가 매출: +{strategy.projected_revenue:,}원 "
                f"(집행 비용 {strategy.estimated_cost:,}원 대비 ROI {strategy.expected_roi_ratio}배)"
            ),
        }

        return PlatformMarketingPlan(
            plan_id=f"PLAN_{uuid.uuid4().hex[:8].upper()}",
            entity_name=state.entity_name,
            domain=state.domain,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            context_vector=context,
            strategy=strategy,
            channels=channels,
            all_compliant=all_compliant,
            summary_financials=summary_financials,
            attribution=attribution,
        )

    @classmethod
    def execute_campaign(
        cls,
        plan: PlatformMarketingPlan,
        selected_channels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Closed-loop execution dispatcher.

        컴플라이언스를 통과하지 못한 채널은 **발송하지 않는다.** 문서 13이 처음
        적어둔 원칙이 실행 코드에서 지켜지는 지점이다.

        다만 두 종류의 위반을 구분한다. 표시광고법 위반은 본문이 이미 교정본으로
        치환되어 있으므로 발송을 막지 않는다(교정 사실을 사장님이 볼 수 있다).
        반면 **데이터 라이선스 출처 표기 누락은 교정본이 존재하지 않는다.**
        표기 자체가 없으므로 보내면 그대로 위반이다. 이것만 막는다.
        """
        from aim.core.compliance_engine import ATTRIBUTION_RULE_CATEGORY

        target_channels = selected_channels or list(plan.channels.keys())
        blocking = sorted(
            {
                key
                for key in target_channels
                if key in plan.channels
                for v in plan.channels[key].compliance_report.violations
                if v.rule_category == ATTRIBUTION_RULE_CATEGORY
            }
        )
        if blocking:
            return {
                "status": "BLOCKED",
                "plan_id": plan.plan_id,
                "entity_name": plan.entity_name,
                "dispatched_channels": [],
                "blocked_channels": blocking,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "projected_revenue": 0,
                "message": (
                    f"{len(blocking)}개 채널이 데이터 출처 표기 누락으로 발송 보류되었습니다. "
                    "출처를 표기한 뒤 다시 집행하십시오."
                ),
            }

        dispatched_count = len(target_channels)

        return {
            "status": "DISPATCHED",
            "plan_id": plan.plan_id,
            "entity_name": plan.entity_name,
            "dispatched_channels": target_channels,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "projected_revenue": plan.strategy.projected_revenue,
            "message": f"{dispatched_count}개 채널로 실시간 타임어택 마케팅이 성공적으로 송출되었습니다.",
        }

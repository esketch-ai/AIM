"""AIM (AI Platform Initiative) - B2B SaaS Domain Plugin
Encapsulates domain logic for software products, cloud web apps, and developer platforms.
Models feature release virality, onboarding drop-off, and MRR expansion.
"""

from typing import List, Dict, Any
from aim.domains.base import BaseDomainPlugin
from aim.schema import BusinessState, Context6D, StrategyObjective


class B2BSaaSDomainPlugin(BaseDomainPlugin):
    @property
    def domain_key(self) -> str:
        return "b2b_saas"

    @property
    def display_name(self) -> str:
        return "IT / B2B SaaS 웹앱 플랫폼"

    def evaluate_triggers(self, state: BusinessState, context: Context6D) -> StrategyObjective:
        seat_unit_price = state.unit_price or 200000  # monthly team subscription
        churn_risk_count = state.pending_leads_count or 120

        # Converts ~12% of inactive/churn-risk free tier teams
        converted_teams = max(5, int(churn_risk_count * 0.12))
        proj_rev = seat_unit_price * converted_teams
        cost = 50000  # Email/Slack automation and product hunt boost

        return StrategyObjective(
            objective_type="VIRAL_EXPANSION",
            campaign_title=f"🚀 [{context.situation}] 트리거 & [{context.milestone}] 온보딩 이탈 방어",
            target_persona=state.target_audience,
            core_narrative=f"반복 업무 제거와 {state.core_usps[0] if state.core_usps else '실시간 자동화'}를 통한 팀 생산성 혁신",
            incentive_offer="신규 메이저 기능 14일 무료 트라이얼 + 팀 전용 스타터 템플릿 즉시 복사",
            urgency_level="HIGH",
            recommended_channels=["blog", "social", "direct"],
            projected_additional_units=converted_teams,
            projected_revenue=proj_rev,
            estimated_cost=cost,
            expected_roi_ratio=round((proj_rev - cost) / cost, 1) if cost > 0 else 0.0,
        )

    def get_compliance_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "SAAS_GDPR_SECURITY",
                "authority": "글로벌 GDPR & 국내 개인정보보호법",
                "prohibited": ["전 세계 1위 협업툴", "해킹 100% 원천 차단"],
                "required_disclosure": "SOC2 Type2 및 엔터프라이즈 데이터 암호화 표준 준수",
            }
        ]

    def get_channel_blueprint(
        self,
        channel_key: str,
        state: BusinessState,
        strategy: StrategyObjective,
        context: Context6D,
        tone: str = "DEFAULT",
    ) -> Dict[str, Any]:
        usp_txt = " • ".join(state.core_usps[:2]) if state.core_usps else "깃허브 이슈 자동 동기화"

        if channel_key == "blog":
            headline = f"[Product Release] {state.entity_name}: {context.situation} 해결을 위한 AI 에이전트 업데이트"
            points = [
                f"핵심 아키텍처 및 연동: {usp_txt}",
                f"{context.season} 분기 목표 달성을 위한 스프린트 가속화",
                f"도입 효과: {strategy.incentive_offer}",
            ]
            cta = "지금 무료 워크스페이스를 생성하고 팀 생산성을 측정해보세요."
        elif channel_key == "social":
            headline = f"🚀 Product Hunt Featured! {context.generation}를 위한 {state.entity_name} 릴리즈"
            points = [
                f"{usp_txt} 기능 공식 오픈",
                f"지루한 수동 입력을 끝내는 자동화 워크플로우",
                f"{strategy.incentive_offer}",
            ]
            cta = "GitHub 레포지토리 또는 웹사이트에서 지금 바로 시작해보세요 ⚡"
        else:  # direct (onboarding email/webhook)
            headline = f"📧 [{state.entity_name}] {context.milestone} 단계 고객님을 위한 3분 스타터 킷"
            points = [
                f"{context.situation}에 꼭 필요한 추천 워크플로우",
                f"팀원 초대 시 제공되는 혜택: {strategy.incentive_offer}",
            ]
            cta = "클릭 한 번으로 팀 대시보드로 이동하여 템플릿을 복사하세요."

        return {
            "headline": headline,
            "points": points,
            "cta": cta,
            "hashtags": ["#B2BSaaS", "#Productivity", f"#{state.entity_name.split()[0]}"],
        }

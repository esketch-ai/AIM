"""AIM (AI Platform Initiative) - B2B SaaS Domain Plugin
Encapsulates domain logic for software products, cloud web apps, and developer platforms.
Models feature release virality, onboarding drop-off, and MRR expansion.
"""

from datetime import datetime
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
                "prohibited": [
                    "전 세계 1위 협업툴",
                    "해킹 100% 원천 차단",
                    "무결점 보안",
                    "데이터 유출 0% 보장",
                ],
                "required_disclosure": "※ SOC2 Type2 및 엔터프라이즈 데이터 암호화 표준 준수",
            }
        ]

    @classmethod
    def parse_github_release_to_viral(
        cls,
        product_name: str,
        version: str,
        release_notes: str,
    ) -> Dict[str, Any]:
        """Parses GitHub release notes into 4-channel viral GTM marketing payloads (Product Hunt, Twitter/X, LinkedIn, Changelog)."""
        lines = [line.strip() for line in release_notes.strip().split("\n") if line.strip()]
        features = [
            l.lstrip("-*# ")
            for l in lines
            if any(k in l.lower() for k in ["feat", "add", "new", "기능", "지원", "추가", "개선"])
        ]
        if not features and lines:
            features = [lines[0].lstrip("-*# ")]

        feat_summary = " & ".join(features[:2]) if features else "생산성 향상 신규 업데이트"

        product_hunt = {
            "title": f"{product_name} {version} 🚀",
            "tagline": f"Supercharge your team productivity with {feat_summary}",
            "maker_comment": (
                f"Hey Product Hunt! 👋 We are excited to launch {product_name} {version}.\n"
                f"Key upgrades: {', '.join(features[:3])}.\n"
                f"Try our 14-day free workspace trial and let us know your feedback!"
            ),
        }

        twitter_thread = [
            f"1/3 🚀 {product_name} {version} is finally live!\nHere is everything new in this release 🧵👇",
            f"2/3 ✨ What's New:\n" + "\n".join([f"• {f}" for f in features[:3]]),
            f"3/3 ⚡ Ready to upgrade your workflow? Get started for free today: https://github.com/releases/tag/{version} #B2BSaaS #ProductHunt",
        ]

        linkedin_post = (
            f"Excited to announce the official release of {product_name} {version}!\n\n"
            f"Today's release focuses on eliminating developer friction with {feat_summary}.\n\n"
            f"Key Highlights:\n" + "\n".join([f"• {f}" for f in features[:4]]) + "\n\n"
            f"Empower your engineering and product teams with frictionless automation. Link in comments! 🚀"
        )

        changelog = (
            f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n"
            f"### 🚀 New Features\n" + "\n".join([f"- {f}" for f in features])
        )

        return {
            "version": version,
            "product_name": product_name,
            "product_hunt": product_hunt,
            "twitter_thread": twitter_thread,
            "linkedin_post": linkedin_post,
            "changelog": changelog,
        }

    @classmethod
    def generate_churn_killer_nudge(
        cls, product_name: str, user_role: str, inactive_days: int = 3
    ) -> Dict[str, Any]:
        """Generates churn prevention onboarding trigger based on inactivity."""
        return {
            "campaign_type": "CHURN_DEFENSE_TRIGGER",
            "inactive_days": inactive_days,
            "target_role": user_role,
            "subject": f"[{product_name}] {user_role}님을 위한 3분 빠른 시작 가이드 템플릿 🎁",
            "body": (
                f"{user_role}님, {product_name}에 가입해 주셔서 감사합니다.\n"
                f"초기 설정의 번거로움을 덜어드리기 위해 {user_role} 직무에 최적화된 "
                f"샘플 프로젝트 템플릿과 3분 튜토리얼을 준비했습니다.\n"
                f"클릭 한 번으로 즉시 복사하여 워크스페이스를 시작해 보세요!"
            ),
            "cta": "샘플 워크스페이스 원클릭 복사하기",
        }

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

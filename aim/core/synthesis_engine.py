"""AIM (AI Platform Initiative) - Dynamic Content Synthesis Engine
Synthesizes channel-specific structured copies from domain blueprints, strategy objectives, and 6D context.
"""

from typing import Dict
from aim.schema import BusinessState, Context6D, StrategyObjective, ChannelPayload
from aim.core.domain_registry import DomainRegistry
from aim.core.compliance_engine import ComplianceEngine
from aim.generator import clean_markdown_spacing


class ContentSynthesisEngine:
    """Composes dynamic markdown marketing payloads for omni-channels without static text templates."""

    CHANNEL_NAMES = {
        "blog": "SEO 롱폼 블로그 / 기술 백서",
        "social": "SNS 피드 / 숏폼 / 글로벌 인덱싱",
        "direct": "1:1 다이렉트 넛지 / 카카오 알림톡 / B2B 오퍼",
    }

    @classmethod
    def synthesize_channel(
        cls,
        channel_key: str,
        state: BusinessState,
        strategy: StrategyObjective,
        context: Context6D,
        tone: str = "MZ_TREND",
    ) -> ChannelPayload:
        plugin = DomainRegistry.get(state.domain)
        if not plugin:
            raise ValueError(f"No domain plugin found for domain '{state.domain}'")

        blueprint = plugin.get_channel_blueprint(channel_key, state, strategy, context, tone)
        headline = blueprint.get("headline", f"[{state.entity_name}] 특별 안내")
        points = blueprint.get("points", [])
        cta = blueprint.get("cta", "지금 바로 확인해보세요.")
        hashtags = blueprint.get("hashtags", [])

        # Compose structured markdown body
        body_lines = [
            f"# {headline}",
            "",
            f"**타깃 고객:** {strategy.target_persona} | **상황:** {context.situation}",
            "",
            "---",
            "",
            "## 💡 주요 핵심 안내 및 혜택",
        ]
        for pt in points:
            body_lines.append(f"- {pt}")

        body_lines.extend([
            "",
            "---",
            "",
            f"> **실시간 혜택 안내:**  \n> \"{strategy.incentive_offer or '사전 예약 시 특별 혜택 제공'}\"",
            "",
            f"**참여 / 예약:** {cta}",
        ])

        # 데이터 라이선스 출처 표기 (CC BY 4.0). 기상 데이터를 실제로 썼을 때만
        # 붙인다. 항상 붙이면 표기가 노이즈가 되어 진짜 의무를 흐리게 만든다.
        attribution = context.provenance.required_attribution
        if attribution:
            body_lines.extend(["", "---", "", f"*{attribution}*"])

        raw_body = clean_markdown_spacing("\n".join(body_lines))

        # Regulatory compliance audit. 출처 표기 누락도 위반으로 판정한다.
        compliance_rep = ComplianceEngine.audit(
            raw_body, state.domain, required_attribution=attribution
        )

        return ChannelPayload(
            channel_key=channel_key,
            channel_display_name=cls.CHANNEL_NAMES.get(channel_key, channel_key),
            headline=headline,
            body=compliance_rep.sanitized_text,
            call_to_action=cta,
            hashtags=hashtags,
            compliance_report=compliance_rep,
            attribution=attribution,
        )

    @classmethod
    def synthesize_all(
        cls,
        state: BusinessState,
        strategy: StrategyObjective,
        context: Context6D,
        tone: str = "MZ_TREND",
    ) -> Dict[str, ChannelPayload]:
        channels = {}
        for c_key in ["blog", "social", "direct"]:
            channels[c_key] = cls.synthesize_channel(
                c_key, state, strategy, context, tone
            )
        return channels

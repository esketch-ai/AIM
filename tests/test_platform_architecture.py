"""Tests for AIM Platform Core Architecture
Validates:
1. ContextEngine (Dynamic 6D Context Sensing)
2. DomainRegistry & BaseDomainPlugin Extensibility
3. StrategyEngine (Operational Triggers -> Campaign Goals & Financial ROI)
4. ComplianceEngine (Multi-tier deterministic regulatory guardrails)
5. ContentSynthesisEngine (Omni-channel synthesis)
6. AIMPlatform Kernel (End-to-End Orchestration & Execution)
"""

import unittest
from aim.schema import BusinessState, Context6D, StrategyObjective
from aim.core.context_engine import ContextEngine
from aim.core.domain_registry import DomainRegistry
from aim.core.strategy_engine import StrategyEngine
from aim.core.compliance_engine import ComplianceEngine
from aim.core.synthesis_engine import ContentSynthesisEngine
from aim.core.platform import AIMPlatform
from aim.domains.base import BaseDomainPlugin


class CustomPetCarePlugin(BaseDomainPlugin):
    """Demonstrates open-closed plugin extensibility for a new arbitrary industry."""
    @property
    def domain_key(self) -> str:
        return "pet_care"

    @property
    def display_name(self) -> str:
        return "반려동물 / 펫호텔·미용"

    def evaluate_triggers(self, state: BusinessState, context: Context6D) -> StrategyObjective:
        return StrategyObjective(
            objective_type="CAPACITY_RESCUE",
            campaign_title=f"🐶 [{context.situation}] 긴급 펫호텔 케어 & [{context.milestone}] 픽업 서비스",
            target_persona=state.target_audience,
            core_narrative="반려견 맞춤 1:1 케어와 안심 CCTV",
            incentive_offer="첫 이용 시 스파 서비스 무료 제공",
            urgency_level="MEDIUM",
            recommended_channels=["social", "direct", "blog"],
            projected_additional_units=8,
            projected_revenue=state.unit_price * 8,
            estimated_cost=15000,
            expected_roi_ratio=15.0,
        )

    def get_compliance_rules(self):
        return [
            {
                "rule_id": "VET_CARE_ACT",
                "authority": "동물보호법 및 수의사법",
                "prohibited": ["의료 처치 100% 보장", "수의사 진료 무료"],
            }
        ]

    def get_channel_blueprint(self, channel_key, state, strategy, context, tone="DEFAULT"):
        return {
            "headline": f"[{context.region}] 안심 펫케어 '{state.entity_name}'",
            "points": ["1:1 맞춤 케어", strategy.incentive_offer],
            "cta": "네이버 예약으로 호텔 슬롯을 예약하세요.",
            "hashtags": ["#펫호텔", "#반려견동반"],
        }


class TestPlatformArchitecture(unittest.TestCase):
    def test_context_engine_dynamic_sensing(self):
        ctx = ContextEngine.build_context(
            domain="fnb",
            location="서울 성동구 성수동 1가",
            target_audience="2030 MZ세대",
            situation="오후 15시 우천 시작",
            milestone="커플 100일 기념일",
        )
        self.assertIn("성수", ctx.region)
        self.assertIn("우천", ctx.situation)
        self.assertIn("100일", ctx.milestone)
        self.assertTrue(bool(ctx.season))
        self.assertTrue(bool(ctx.era))

    def test_domain_registry_extensibility(self):
        # Register new custom domain plugin
        custom_plugin = CustomPetCarePlugin()
        DomainRegistry.register(custom_plugin)

        retrieved = DomainRegistry.get("pet_care")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.display_name, "반려동물 / 펫호텔·미용")

    def test_strategy_engine_evaluation(self):
        state = BusinessState(
            domain="medical",
            entity_name="청담 예인 피부과",
            location="서울 강남구 신논현",
            target_audience="3040 직장인",
            core_usps=["전문의 1:1 맞춤 진단", "정품 정량 100% 개봉"],
            idle_capacity_rate=0.1,
            trigger_event="노쇼 1건 발생",
            unit_price=250000,
            pending_leads_count=50,
        )
        ctx = ContextEngine.build_context(
            domain="medical",
            location=state.location,
            target_audience=state.target_audience,
        )
        strategy = StrategyEngine.evaluate(state, ctx)
        self.assertEqual(strategy.objective_type, "RETENTION_RECALL")
        self.assertGreater(strategy.projected_revenue, 1000000)
        self.assertGreater(strategy.expected_roi_ratio, 10.0)

    def test_compliance_engine_multi_domain(self):
        # Medical violation
        med_violating = "저희 병원은 부작용 전혀 없음 및 국내 최고의 시술을 자랑합니다."
        rep = ComplianceEngine.audit(med_violating, domain="medical")
        self.assertFalse(rep.is_compliant)
        violated_terms = [v.original_term for v in rep.violations]
        self.assertIn("부작용 전혀 없음", violated_terms)
        self.assertIn("최고", violated_terms)

        # Compliant text
        clean = "정품 정량 원칙을 준수하는 전문의 1:1 맞춤 진료 플랜입니다."
        clean_rep = ComplianceEngine.audit(clean, domain="medical")
        self.assertTrue(clean_rep.is_compliant)

    def test_content_synthesis_engine(self):
        state = BusinessState(
            domain="b2b_saas",
            entity_name="태스크플로우 (TaskFlow)",
            location="판교 테크노밸리",
            target_audience="개발팀장 & PM",
            core_usps=["GitHub 이슈 실시간 동기화", "AI 자동 스프린트 회고"],
            idle_capacity_rate=0.2,
            trigger_event="v3.0 신규 릴리즈 배포 완료",
            unit_price=180000,
            pending_leads_count=80,
        )
        ctx = ContextEngine.build_context(
            domain=state.domain,
            location=state.location,
            target_audience=state.target_audience,
            situation=state.trigger_event,
        )
        strategy = StrategyEngine.evaluate(state, ctx)
        channels = ContentSynthesisEngine.synthesize_all(state, strategy, ctx)

        self.assertIn("blog", channels)
        self.assertIn("social", channels)
        self.assertIn("direct", channels)
        for c in channels.values():
            self.assertTrue(bool(c.headline))
            self.assertTrue(bool(c.body))
            self.assertTrue(c.compliance_report.is_compliant)

    def test_aim_platform_end_to_end(self):
        state = BusinessState(
            domain="manufacturing",
            entity_name="한국정밀공업",
            location="경남 창원 산단",
            target_audience="해외 완성차 부품 구매팀",
            core_usps=["5축 머시닝 센터 공차 ±0.005mm", "IATF 16949 인증"],
            idle_capacity_rate=0.4,
            trigger_event="사출 2호 라인 유휴 캐파 40% 발생",
            unit_price=30000000,
            pending_leads_count=2,
        )
        plan = AIMPlatform.plan_campaign(state=state)
        self.assertTrue(plan.plan_id.startswith("PLAN_"))
        self.assertEqual(plan.domain, "manufacturing")
        self.assertEqual(plan.strategy.projected_revenue, 60000000)
        self.assertIn("blog", plan.channels)

        exec_res = AIMPlatform.execute_campaign(plan)
        self.assertEqual(exec_res["status"], "DISPATCHED")
        self.assertEqual(exec_res["projected_revenue"], 60000000)


if __name__ == "__main__":
    unittest.main()

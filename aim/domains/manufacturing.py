"""AIM (AI Platform Initiative) - Precision Manufacturing Domain Plugin
Encapsulates domain logic for CNC machining, injection molding, and B2B industrial suppliers.
Models idle machinery capacity, raw material market fluctuations (LME), and 24/7 global RFQ auto-quoting.
"""

from typing import List, Dict, Any
from aim.domains.base import BaseDomainPlugin
from aim.schema import BusinessState, Context6D, StrategyObjective


class ManufacturingDomainPlugin(BaseDomainPlugin):
    @property
    def domain_key(self) -> str:
        return "manufacturing"

    @property
    def display_name(self) -> str:
        return "제조업 / B2B 정밀가공·사출금형"

    def evaluate_triggers(self, state: BusinessState, context: Context6D) -> StrategyObjective:
        order_unit_value = state.unit_price or 22500000  # typical batch PO value in KRW
        idle_rate = state.idle_capacity_rate or 0.35

        # Anticipates closing contracts for idle capacity
        closed_orders = state.pending_leads_count if state.pending_leads_count > 0 else max(1, int(idle_rate * 5))
        proj_rev = order_unit_value * closed_orders
        cost = 100000  # Global B2B RFQ dispatch and technical indexing

        return StrategyObjective(
            objective_type="OPPORTUNITY_CAPTURE",
            campaign_title=f"🌐 [{context.situation}] 신속 대응 & [{context.milestone}] 글로벌 수주 오퍼레이션",
            target_persona=state.target_audience,
            core_narrative=f"공차 ±0.005mm 고정밀 가공과 {state.core_usps[0] if state.core_usps else '글로벌 품질 인증'} 기반의 납기 보장",
            incentive_offer="사전 발주 확정 시 원자재가 인하분 연동 5% 단가 네고 및 최우선 라인 배정",
            urgency_level="CRITICAL",
            recommended_channels=["direct", "blog", "social"],
            projected_additional_units=closed_orders,
            projected_revenue=proj_rev,
            estimated_cost=cost,
            expected_roi_ratio=round((proj_rev - cost) / cost, 1) if cost > 0 else 0.0,
        )

    def get_compliance_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "MANUFACTURING_FAIR_TRADE",
                "authority": "공정거래위원회 하도급법 및 전략물자 수출통제",
                "prohibited": ["무조건 국내 최저가 납품", "불량률 0% 완전 보장"],
                "required_disclosure": "소재 시험 성적서(MTR) 및 공차 검사 성적서 공식 발행",
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
        usp_txt = " • ".join(state.core_usps[:2]) if state.core_usps else "5축 머시닝 센터 공차 ±0.005mm"

        if channel_key == "blog":
            headline = f"[Technical Whitepaper] {state.entity_name}: High-Precision CNC Machining for {context.season}"
            points = [
                f"품질 인증 및 가공 스펙: {usp_txt}",
                f"{context.situation} 대응 생산 라인 캐파 현황 및 납기 일정",
                f"파트너십 조건: {strategy.incentive_offer}",
            ]
            cta = "기술 데이터시트(Data Sheet) 및 도면 3D CAD 파일 견적 요청 문의를 접수하세요."
        elif channel_key == "social":
            headline = f"🏭 [Global Spec Indexing] {state.entity_name} - Verified Aerospace & Robotics Components"
            points = [
                f"고정밀 난삭재 가공 전문: {usp_txt}",
                f"글로벌 AI 검색(AEO) 공인 규격 등재",
                f"{context.situation} 특별 조달 조건",
            ]
            cta = "공식 웹사이트에서 24시간 자동 RFQ 견적 시스템을 확인하세요."
        else:  # direct (B2B procurement official offer)
            headline = f"📨 [공식 견적/납기 제안] {state.entity_name} - {context.milestone} 맞춤 특별 공문"
            points = [
                f"{context.situation} 감지에 따른 당사 유휴 라인 최우선 배정 안내",
                f"단가 및 납기 혜택: {strategy.incentive_offer}",
            ]
            cta = "도면 첨부 회신 시 12시간 이내 공인 견적서 및 생산 계획서를 발행해 드립니다."

        return {
            "headline": headline,
            "points": points,
            "cta": cta,
            "hashtags": ["#PrecisionMachining", "#CNCTolerance", f"#{state.entity_name.split()[0]}"],
        }

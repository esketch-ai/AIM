"""AIM (AI Platform Initiative) - Precision Manufacturing Domain Plugin
Encapsulates domain logic for CNC machining, injection molding, and B2B industrial suppliers.
Models idle machinery capacity, raw material market fluctuations (LME), and 24/7 global RFQ auto-quoting.
"""

from typing import List, Dict, Any, Optional
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
                "prohibited": [
                    "무조건 국내 최저가 납품",
                    "불량률 0% 완전 보장",
                    "납기 지연 배상 면책",
                    "100% 무결점 보증",
                ],
                "required_disclosure": "※ 소재 시험 성적서(MTR) 및 공차 검사 성적서 공식 발행",
            }
        ]

    @classmethod
    def generate_global_rfq_response(
        cls,
        company_name: str,
        buyer_country: str,
        part_name: str,
        tolerance_spec: str = "±0.005mm",
        certifications: Optional[List[str]] = None,
        moq: int = 500,
        lead_time_days: int = 14,
    ) -> Dict[str, Any]:
        """Generates 24/7 global RFQ technical proposal in response to foreign buyer inquiry."""
        certs = ", ".join(certifications or ["ISO 9001:2015", "IATF 16949"])
        return {
            "rfq_response_type": "24_7_GLOBAL_RFQ_PROPOSAL",
            "buyer_country": buyer_country,
            "part_name": part_name,
            "headline": f"Official Technical Proposal: Precision {part_name} - {company_name}",
            "specifications": {
                "machining_tolerance": tolerance_spec,
                "certifications": certs,
                "moq": moq,
                "estimated_lead_time": f"{lead_time_days} business days",
                "inspection": "CMM 3D Coordinate Inspection & Material Test Report (MTR)",
            },
            "cover_letter": (
                f"Dear Procurement Manager ({buyer_country}),\n\n"
                f"Thank you for your RFQ regarding {part_name}. {company_name} is fully equipped "
                f"with 5-axis CNC machining centers achieving precision tolerance of {tolerance_spec}.\n"
                f"We hold {certs} certifications and guarantee full material traceability with official MTR.\n\n"
                f"Please find our initial technical feasibility and manufacturing schedule enclosed."
            ),
            "disclosure": "※ 소재 시험 성적서(MTR) 및 공차 검사 성적서 공식 발행",
            "cta": "Request CAD Drawing Review & Formal Quotation Sheet",
        }

    @classmethod
    def generate_lme_raw_material_deal(
        cls,
        company_name: str,
        material_name: str,
        price_drop_pct: float,
        discount_offer_pct: float = 5.0,
    ) -> Dict[str, Any]:
        """Generates B2B flash purchase offer triggered by LME raw material market dips."""
        return {
            "campaign_type": "LME_RAW_MATERIAL_FLASH_DEAL",
            "material": material_name,
            "price_drop_pct": price_drop_pct,
            "headline": f"📢 [{company_name}] {material_name} 시세 하락 연동 긴급 사전발주 프로모션",
            "narrative": (
                f"런던금속거래소(LME) {material_name} 시세 {price_drop_pct:.1f}% 하락에 연동하여, "
                f"차기 분기 물량을 선발주하시는 고객사 대상 {discount_offer_pct:.1f}% 특별 단가 네고 및 "
                f"당사 정밀 가공 라인 우선 배정 혜택을 제공합니다."
            ),
            "disclosure": "※ 소재 시험 성적서(MTR) 및 공차 검사 성적서 공식 발행",
            "cta": "도면 첨부 및 특별 단가 확정 회신",
        }

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

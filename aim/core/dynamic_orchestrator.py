"""
AIM Dynamic Orchestrator & Signal Bus (aim/core/dynamic_orchestrator.py)
------------------------------------------------------------------------
Organic Event-Driven Kernel connecting:
1. Signal Sensing (Weather/Idle, Competitor Weakness, Rank Drop, Crisis Review, POS Slot)
2. Strategy Orchestration (Domain-specific rules)
3. Value Compression & 15s Storyboard Brief Generation
4. Creator Matching & Escrow Pricing (10% subscriber discount)
5. Omnichannel Synthesis & Compliance Guardrails
6. Value Attribution & Master FinOps Feedback
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from aim.core.value_compressor import ValueCompressor, ValueCompressionRequest
from aim.core.brief_generator import BriefGenerator, BriefQuestionnaireInput
from aim.matching.creator_network import creator_network, MatchRequest


class DynamicTriggerSignal(BaseModel):
    signal_id: str
    tenant_id: str
    signal_type: str  # WEATHER_IDLE, COMPETITOR_WEAKNESS, RANK_DROP, CRISIS_REVIEW, POS_SLOT
    severity: str = "HIGH"  # HIGH, MEDIUM, LOW
    headline: str
    detected_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class OrchestratedActionBundle(BaseModel):
    bundle_id: str
    tenant_id: str
    business_name: str
    domain: str
    trigger_signal: DynamicTriggerSignal
    strategy_summary: str
    compressed_pitch: Dict[str, Any]
    creator_brief: Dict[str, Any]
    omnichannel_copies: Dict[str, Any]
    matched_creators: List[Dict[str, Any]]
    escrow_preview: Dict[str, Any]
    projected_revenue_krw: int
    projected_roi: float
    evidence_tier: str = "C_ILLUSTRATIVE"
    status: str = "READY_FOR_HITL"  # READY_FOR_HITL, APPROVED, DISPATCHED
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class DynamicOrchestrator:
    """The central reactive brain orchestrating multi-layer operations."""

    def __init__(self):
        self.compressor = ValueCompressor()
        self.brief_generator = BriefGenerator()
        self.history: List[OrchestratedActionBundle] = []

    def process_signal(self, signal: DynamicTriggerSignal, subscriber_plan: str = "PRO") -> OrchestratedActionBundle:
        bundle_id = f"BUNDLE_{uuid.uuid4().hex[:8].upper()}"

        # 1. Resolve tenant context presets
        tenant_context = self._resolve_tenant_context(signal.tenant_id)
        domain = tenant_context["domain"]
        business_name = tenant_context["business_name"]
        product_name = tenant_context["default_product"]
        target_audience = tenant_context["default_audience"]
        unit_price = tenant_context["unit_price"]

        # 2. Dynamic strategy formulation based on signal type
        strategy_info = self._formulate_strategy(signal, product_name, unit_price, domain)

        # 3. Value compression (3s Hook + 10s Numbers + Single CTA)
        comp_req = ValueCompressionRequest(
            product_name=product_name,
            raw_benefit=strategy_info["core_benefit"],
            target_audience=target_audience,
            pain_point=strategy_info["pain_point"],
            action_type=strategy_info["action_type"],
            contrast_benchmark=strategy_info.get("contrast_benchmark"),
            industry=domain.upper(),
        )
        compressed = self.compressor.compress(comp_req)

        # 4. Standardized 15s Creator Brief generation
        brief_input = BriefQuestionnaireInput(
            product_name=product_name,
            core_benefit=strategy_info["core_benefit"],
            target_audience=target_audience,
            content_format="SHORTS",
            budget_tier="MID_450K",
            industry=domain.upper(),
            tenant_id=signal.tenant_id,
        )
        brief = self.brief_generator.generate(brief_input)

        # 5. Creator Matching & 10% Subscriber Escrow Preview
        match_req = MatchRequest(
            category=domain.upper(),
            content_format="SHORTS",
            budget_tier="MID_450K",
            target_audience=target_audience,
            tenant_id=signal.tenant_id,
            subscriber_plan=subscriber_plan,
        )
        matched_cards = creator_network.match_creators(match_req)
        top_matches = [m.model_dump() for m in matched_cards[:3]]

        top_creator = matched_cards[0] if matched_cards else None
        budget = top_creator.creator.price_krw if top_creator else 450000
        take_rate = 10.0 if subscriber_plan.upper() in ["PRO", "ENTERPRISE"] else 15.0
        platform_fee = int(budget * (take_rate / 100.0))
        creator_total = budget - platform_fee
        base_payout = int(creator_total * 0.70)
        bonus_payout = creator_total - base_payout

        escrow_preview = {
            "top_creator_name": top_creator.creator.name if top_creator else "서울핫플스케치",
            "total_budget": budget,
            "take_rate_pct": take_rate,
            "platform_fee": platform_fee,
            "creator_base_payout": base_payout,
            "creator_bonus_payout": bonus_payout,
            "fast_track_hours_left": 24,
            "subscriber_discount_applied": subscriber_plan.upper() in ["PRO", "ENTERPRISE"],
        }

        # 6. Omnichannel Copy Synthesis
        omnichannel = {
            "kakao_alert": {
                "headline": f"[{business_name}] {strategy_info['headline']}",
                "body": f"{compressed.pain_point_strike}\n{compressed.metaphor_and_number}\n\n👉 {compressed.direct_cta}",
                "cta_button": compressed.direct_cta,
            },
            "instagram_reels": {
                "caption": f"{compressed.pain_point_strike} 🔥 {product_name}\n\n#성수핫플 #마케팅OS #타임특가",
                "hook_3sec": compressed.pain_point_strike,
            },
            "naver_blog": {
                "title": f"[{business_name}] {strategy_info['headline']} 솔직 방문 후기",
                "summary": compressed.full_compressed_pitch,
            },
        }

        # 7. Projected Financials & ROI
        projected_units = strategy_info["projected_units"]
        projected_revenue = projected_units * unit_price
        total_investment = 49000  # Monthly Pro subscription baseline
        roi_ratio = round(projected_revenue / total_investment, 1) if total_investment > 0 else 10.0

        bundle = OrchestratedActionBundle(
            bundle_id=bundle_id,
            tenant_id=signal.tenant_id,
            business_name=business_name,
            domain=domain,
            trigger_signal=signal,
            strategy_summary=strategy_info["summary"],
            compressed_pitch=compressed.model_dump(),
            creator_brief=brief.model_dump(),
            omnichannel_copies=omnichannel,
            matched_creators=top_matches,
            escrow_preview=escrow_preview,
            projected_revenue_krw=projected_revenue,
            projected_roi=roi_ratio,
            evidence_tier="C_ILLUSTRATIVE",
            status="READY_FOR_HITL",
        )

        self.history.append(bundle)
        return bundle

    def _resolve_tenant_context(self, tenant_id: str) -> Dict[str, Any]:
        mapping = {
            "TENANT_001": {
                "business_name": "성수 아뜰리에 베이커리 & 카페",
                "domain": "FNB",
                "default_product": "시그니처 바질 소금빵",
                "default_audience": "2030 성수동 직장인 및 디저트 러버",
                "unit_price": 24000,
            },
            "TENANT_002": {
                "business_name": "강남 리엔 피부과의원",
                "domain": "MEDICAL",
                "default_product": "1:1 리프팅 & 피부 장벽 케어",
                "default_audience": "3040 강남 오피스 직장인",
                "unit_price": 350000,
            },
            "TENANT_003": {
                "business_name": "청담 아우라 헤어살롱",
                "domain": "BEAUTY",
                "default_product": "시그니처 레이어드 펌 & 두피 스파",
                "default_audience": "2030 청담/압구정 여성 고객",
                "unit_price": 180000,
            },
            "TENANT_004": {
                "business_name": "플로우독 (FlowDoc) SaaS",
                "domain": "B2B_SAAS",
                "default_product": "FlowDoc 올인원 실시간 문서 협업 솔루션",
                "default_audience": "IT 스타트업 개발/기획 리드",
                "unit_price": 500000,
            },
            "TENANT_005": {
                "business_name": "대진정밀공업 (CNC·사출 가공)",
                "domain": "MANUFACTURING",
                "default_product": "ISO 인증 5축 CNC 초정밀 가공 솔루션",
                "default_audience": "대기업 구매팀 및 설계 엔지니어",
                "unit_price": 1500000,
            },
        }
        return mapping.get(tenant_id, mapping["TENANT_001"])

    def _formulate_strategy(self, signal: DynamicTriggerSignal, product: str, unit_price: int, domain: str) -> Dict[str, Any]:
        stype = signal.signal_type.upper()
        if stype == "WEATHER_IDLE":
            return {
                "headline": "☔ 비 오는 날 3시간 깜짝 번개! 빵 포장 시 오트라떼 1+1",
                "summary": "15시 비 예보로 인한 워크인 유휴 좌석 35% 방어 타임어택 가동",
                "pain_point": "비 오는 날 축축하고 나른한 오후, 눅눅한 빵에 실망하셨나요?",
                "core_benefit": "프랑스 AOP 고메버터 48%로 방금 구워낸 바삭한 힐링",
                "action_type": "DISCOUNT_COUPON",
                "contrast_benchmark": "일반 베이커리 대비 48% 버터 함량 극강 풍미",
                "projected_units": 10,
            }
        elif stype == "COMPETITOR_WEAKNESS":
            return {
                "headline": "✨ 경쟁사 불만 속성 반사이익! 천연발효 사워도우 & 넓은 테라스",
                "summary": "반경 250m B카페의 '느끼하고 좁다'는 고객 불만을 흡수하는 반사이익 역공 전략",
                "pain_point": "너무 달고 느끼한 디저트와 좁은 좌석에 지치셨나요?",
                "core_benefit": "속이 편안한 100% 천연발효 사워도우와 쾌적한 야외 테라스",
                "action_type": "VISIT",
                "contrast_benchmark": "옆집 B카페 불만 고객 흡수",
                "projected_units": 15,
            }
        elif stype == "RANK_DROP":
            return {
                "headline": "🚀 스마트플레이스 1위 탈환! '반려동물 동반/AOP버터' 영수증 리뷰 이벤트",
                "summary": "네이버 4위에서 1위로 도약하기 위한 핵심 키워드 방문자 영수증 리뷰 5건 집중 확보",
                "pain_point": "어디가 진짜 맛집인지 검색 결과 광고에 피로하셨나요?",
                "core_benefit": "실제 결제 손님들의 100% 찐 영수증 인증 리뷰",
                "action_type": "DISCOUNT_COUPON",
                "contrast_benchmark": "사기성 대행사 월 150만원 대신 자체 영수증 리뷰 1위 처방",
                "projected_units": 8,
            }
        elif stype == "CRISIS_REVIEW":
            return {
                "headline": "🛡️ 1점 악성 리뷰 품격 방어! 정중 사과 및 재방문 케어",
                "summary": "웨이팅/품절 불만에 대한 3단계 품격 대응(사과-원인규명-재방문 보장)으로 잠재 고객 신뢰 회복",
                "pain_point": "귀한 걸음 하셨는데 조기 품절로 실망을 안겨드렸나요?",
                "core_benefit": "당일 생산 당일 소진 원칙을 지키며 사전 예약 시스템 도입",
                "action_type": "RESERVATION",
                "contrast_benchmark": "감정적 싸움 대신 품격 있는 사과로 별점 평판 방어",
                "projected_units": 5,
            }
        else:  # POS_SLOT or default
            return {
                "headline": "⚡ 평일 낮 유휴 슬롯 40% 방어 타임어택 프로모션",
                "summary": "피크타임 이후 빈 테이블을 단골 알림톡 및 숏폼 릴스로 즉시 채우는 방어전",
                "pain_point": "오후 시간 빈 좌석 때문에 매장 임대료가 부담스러우셨나요?",
                "core_benefit": "오후 14시~17시 한정 단골 타임어택 혜택",
                "action_type": "DISCOUNT_COUPON",
                "contrast_benchmark": "유휴 좌석 방치 대비 순매출 24만원 추가 확보",
                "projected_units": 10,
            }


# Singleton Orchestrator Instance
dynamic_orchestrator = DynamicOrchestrator()

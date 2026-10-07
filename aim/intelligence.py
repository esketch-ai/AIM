"""AIM (AI Platform Initiative) - Intelligence & War Room Engine
Powers real revenue-driving services that business owners actually pay for:
1. Competitor Radar (동네 반경 1km 경쟁 매장 실시간 스파이 & 반사이익 공략)
2. Flash Revenue Booster (날씨/유휴 시간대 기습 타임어택 매출 부스터)
3. Search Rank Doctor (네이버 스마트플레이스 & ChatGPT 1순위 탈환 처방전)
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from aim.schema import EvidenceTier


class CompetitorInsight(BaseModel):
    competitor_name: str
    distance: str
    recent_move: str
    customer_weakness: str  # 경쟁사 최근 악평/약점
    counter_strategy: str   # 우리 매장의 반사이익 공략 작전
    evidence_tier: EvidenceTier = Field(
        default=EvidenceTier.C_ILLUSTRATIVE,
        description="경쟁사 실측 수집기(P2) 구현 전까지 항상 시연값.",
    )


class FlashCampaign(BaseModel):
    trigger_reason: str     # 예: "오후 3시 비 예보 + 테이블 점유율 30% 급감 예상"
    target_audience: str    # 예: "매장 반경 500m 직장인 & 카톡 채널 친구 420명"
    offer_headline: str
    action_benefit: str
    projected_revenue: str  # 예상 추가 결제 창출액
    time_limit: str
    revenue_basis: str = Field(
        default="기상청 실측 예보(P0) 및 POS 정산 실측(P0) 연동 전에는 금액 산출 불가",
        description="금액 추정 근거. 실측 데이터 없이는 금전적 약속으로 사용 금지.",
    )
    evidence_tier: EvidenceTier = Field(
        default=EvidenceTier.C_ILLUSTRATIVE,
        description="실측 컨텍스트 센서 구현 전까지 항상 시연값.",
    )


class RankDiagnostic(BaseModel):
    current_naver_rank: int
    chatgpt_citation_status: str
    missing_keywords: List[str]
    action_prescription: str
    evidence_tier: EvidenceTier = Field(
        default=EvidenceTier.C_ILLUSTRATIVE,
        description="네이버 검색순위 실측 수집기(P1) 구현 전까지 항상 시연값.",
    )


class LocalIntelligenceEngine:
    """Delivers high-impact, revenue-generating insights for store owners."""

    @classmethod
    def get_competitor_radar(cls, category: str = "베이커리/카페") -> List[CompetitorInsight]:
        return [
            CompetitorInsight(
                competitor_name="B카페 성수점",
                distance="250m (도보 3분)",
                recent_move="신메뉴 버터샌드 출시 및 10% 오픈 할인 진행 중",
                customer_weakness="영수증 리뷰에 '너무 달고 느끼하다, 자리가 좁다'는 불만 급증",
                counter_strategy="우리 매장의 '담백한 프랑스 AOP 천연발효 사워도우'와 '넓은 야외 테라스'를 부각하여 반사이익 흡수"
            ),
            CompetitorInsight(
                competitor_name="M베이커리",
                distance="400m (도보 5분)",
                recent_move="오후 1시~3시 아메리카노 1,000원 타임세일 시작",
                customer_weakness="원두 산미에 대한 호불호 및 주문 후 대기 시간 15분 이상 지연",
                counter_strategy="우리는 저가 치킨게임에 휘말리지 않고, '빵+음료 세트 50% 얼리버드'로 객단가 방어"
            ),
            CompetitorInsight(
                competitor_name="C디저트랩",
                distance="650m (도보 8분)",
                recent_move="인스타그램 릴스 인플루언서 협찬 집행 중",
                customer_weakness="포장 배달 시 디저트 모양 붕괴 불만 리뷰 3건 발생",
                counter_strategy="안전하고 꼼꼼한 친환경 패키징 및 당일 생산 당일 폐기 원칙 강조"
            )
        ]

    @classmethod
    def generate_flash_booster(cls, store_name: str) -> FlashCampaign:
        return FlashCampaign(
            trigger_reason="⚠️ 오늘 오후 15시 성수동 비 예보 (강수확률 80%) ➔ 오프라인 워크인 방문객 35% 감소 예상",
            target_audience="매장 반경 1km 직장인 + 카톡 채널 단골 친구 580명",
            offer_headline=f"☔ [비 오는 날 깜짝 번개] {store_name} 갓 구운 빵 포장 시 라떼 1+1!",
            action_benefit="비 오는 시간(14:00~17:00) 내 방문 또는 포장 주문 시 시그니처 오트라떼 무료 증정 쿠폰",
            projected_revenue="빈 테이블 14석 방어 ➔ 오늘 예상 순매출 +420,000원 추가 확보 (시연값)",
            time_limit="오늘 14:00 ~ 17:00 (3시간 한정 타임어택)"
        )

    @classmethod
    def diagnose_search_rank(cls, store_name: str) -> RankDiagnostic:
        return RankDiagnostic(
            current_naver_rank=4,
            chatgpt_citation_status="성수동 조용한 테라스 카페 질의 시 2순위 인용 중",
            missing_keywords=["성수 주차 가능 카페", "성수 글루텐프리 사워도우", "성수 애견동반 브런치"],
            action_prescription=(
                "현재 네이버 스마트플레이스 4위에서 1위로 올라서려면 '반려동물 동반', 'AOP 버터' 관련 방문자 영수증 리뷰 5건이 추가 필요합니다. "
                "결제 고객 대상 '영수증 인증 시 수제 쿠키 증정 이벤트'를 AI가 카톡으로 자동 발송하도록 승인하세요."
            )
        )

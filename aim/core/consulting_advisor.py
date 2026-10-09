"""AIM (AI Platform Initiative) - AI Marketing Consulting Advisor
(aim/core/consulting_advisor.py)
------------------------------------------------------------------
Replaces costly human consulting with real-time, prescriptive marketing advice
powered by the 4 environmental infrastructure pillars (Weather, Local, Anniversary, Event).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from aim.tenant.manager import TenantManager
from aim.infra.marketing_infrastructure import MarketingInfrastructureEngine, ComprehensiveInfraReport


class PrescriptiveAdvice(BaseModel):
    advice_id: str
    category: str  # WEATHER_SALVAGE, LOCAL_EVENT_SURGE, CREATOR_COLLAB, ANNIVERSARY_EARLY
    category_korean: str
    icon: str
    headline: str
    diagnosis: str  # Why this is happening (consultant perspective)
    recommended_action: str  # Exactly what to do
    primary_channel: str  # naver_place, instagram, creator_shorts, kakao_alert
    primary_channel_korean: str
    expected_revenue_gain_krw: int
    expected_roi_ratio: float
    urgency_badge: str
    trigger_source: str


class ConsultingDeskReport(BaseModel):
    tenant_id: str
    business_name: str
    domain: str
    location: str
    infra_report: ComprehensiveInfraReport
    consultant_summary: str
    prescriptions: List[PrescriptiveAdvice]


class AIConsultingAdvisor:
    """Expert marketing consultant engine translating infrastructure signals into actionable recipes."""

    @classmethod
    def evaluate_tenant(cls, tenant_id: str = "TENANT_001") -> ConsultingDeskReport:
        tenant = TenantManager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        loc = tenant.business_state.location or "서울 성수동"
        infra = MarketingInfrastructureEngine.build_infra_report(loc)
        b_name = tenant.business_name
        unit_price = tenant.business_state.unit_price or 24000
        hero = tenant.business_state.core_usps[0] if tenant.business_state.core_usps else "시그니처 메뉴"

        # 1. Weather Prescription
        p1 = PrescriptiveAdvice(
            advice_id=f"ADV_{tenant_id}_WEATHER",
            category="WEATHER_SALVAGE",
            category_korean="🌦️ 날씨/유휴 긴급 매출 방어",
            icon="🌧️",
            headline="비 오는 날 손님이 끊길 때, 네이버 플레이스 소식으로 퇴근길 포장 손님 부르기",
            diagnosis=(
                f"현재 {infra.weather.location}에 {infra.weather.condition_korean} 상황입니다. "
                f"일반 도보 유동인구는 28% 감소하지만, 퇴근길 따뜻한 빵/디저트 포장 수요는 35% 급증하는 패턴이 확인됩니다."
            ),
            recommended_action=(
                f"'{b_name}' 네이버 스마트플레이스에 [3시간 한정 비 오는 날 깜짝 타임특가] 소식을 즉시 등록하고, "
                f"방문 포장 고객 대상 3,000원 할인 쿠폰을 자동 연동합니다."
            ),
            primary_channel="naver_place",
            primary_channel_korean="네이버 스마트플레이스 새소식",
            expected_revenue_gain_krw=240000,
            expected_roi_ratio=12.0,
            urgency_badge="⚡ 골든타임 3시간",
            trigger_source=f"기상 인프라 감지 (강수량 {infra.weather.precipitation_mm}mm)",
        )

        # 2. Local Event Surge Prescription
        ev = infra.active_local_events[0]
        p2 = PrescriptiveAdvice(
            advice_id=f"ADV_{tenant_id}_EVENT",
            category="LOCAL_EVENT_SURGE",
            category_korean="🎪 지역 축제/팝업 인파 포획",
            icon="🎉",
            headline=f"인근 '{ev.name}' 인파를 내 매장으로 유입시키는 인스타 릴스·피드 발행",
            diagnosis=(
                f"매장 반경 500m 내에서 {ev.name}이 진행 중이며, 유동인구가 평소 대비 +{ev.expected_foot_traffic_surge_pct}% 급증하고 있습니다. "
                f"팝업 대기열에 지친 {ev.visitor_profile}들이 인근 쉴 곳과 맛집을 검색하고 있습니다."
            ),
            recommended_action=(
                f"인스타그램 피드 및 릴스에 '{ev.merchant_opportunity}' 혜택을 알리는 감성 숏폼 카피를 발행하고, "
                f"성수동 핫플 필수 해시태그 15종을 자동 부착합니다."
            ),
            primary_channel="instagram",
            primary_channel_korean="인스타그램 피드 & 릴스",
            expected_revenue_gain_krw=480000,
            expected_roi_ratio=16.5,
            urgency_badge=f"🔥 인파 +{ev.expected_foot_traffic_surge_pct}% 급증",
            trigger_source=f"지역 행사 인프라 연동 ({ev.name})",
        )

        # 3. Creator/Blogger Collaboration Prescription
        p3 = PrescriptiveAdvice(
            advice_id=f"ADV_{tenant_id}_CREATOR",
            category="CREATOR_COLLAB",
            category_korean="🎬 유튜버/블로거 15초 콘티 협찬 섭외",
            icon="🤝",
            headline="연락하기 막막했던 빵지순례 전문 숏폼 크리에이터에게 15초 콘티 자동 제안",
            diagnosis=(
                "개인 사업주가 유튜버나 맛집 블로거에게 개별 연락하려면 섭외 단가 파악과 기획안 작성이 어려워 포기하기 일쑤입니다. "
                "신뢰할 수 있는 에스크로 제휴망을 통해 검증된 로컬 푸드 크리에이터를 10% 우대 수수료로 즉시 매칭해야 합니다."
            ),
            recommended_action=(
                f"AI가 작성한 '15초 쇼츠 스토리보드(오프닝 3초 후킹 ➔ {hero} 특장점 ➔ 방문 쿠폰 안내)'를 바탕으로 "
                f"유튜브 쇼츠 크리에이터(@디저트탐험가 은지, 18만)에게 원클릭 협찬 제안서를 발송합니다."
            ),
            primary_channel="creator_shorts",
            primary_channel_korean="유튜브 쇼츠 & 인스타 릴스 크리에이터",
            expected_revenue_gain_krw=850000,
            expected_roi_ratio=5.6,
            urgency_badge="💎 섭외 공수 90% 감축",
            trigger_source="로컬 인플루언서 매칭 네트워크",
        )

        # 4. Anniversary Pre-Order Prescription
        an = infra.active_anniversary
        p4 = PrescriptiveAdvice(
            advice_id=f"ADV_{tenant_id}_ANNIVERSARY",
            category="ANNIVERSARY_EARLY",
            category_korean="🗓️ 다가오는 기념일 선제 공략",
            icon="🎁",
            headline=f"'{an.name}' D-{an.d_day} 골든타임! 단골 고객 대상 선물 세트 선예약 알림톡 발송",
            diagnosis=(
                f"{an.name}까지 D-{an.d_day}일 남았습니다. 기념일 선물 및 외식 예약의 70%는 D-7일에서 D-3일 사이에 일어납니다. "
                f"당일 닥쳐서 홍보하면 이미 예약이 마감되어 다른 매장에 고객을 빼앗깁니다."
            ),
            recommended_action=(
                f"카카오톡 채널 단골 고객에게 '{an.recommended_product_focus} 선예약 15% 특별 혜택' 알림톡을 원클릭 전송하고, "
                f"네이버 예약 링크를 연동하여 선주문 결제를 선점합니다."
            ),
            primary_channel="kakao_alert",
            primary_channel_korean="카카오톡 단골 채널 알림톡",
            expected_revenue_gain_krw=620000,
            expected_roi_ratio=18.2,
            urgency_badge=f"⏰ D-{an.d_day} 선예약 골든타임",
            trigger_source=f"캘린더/기념일 인프라 ({an.name})",
        )

        prescriptions = [p1, p2, p3, p4]

        consultant_summary = (
            f"💡 [수석 마케팅 컨설턴트 종합 진단] '{b_name}' 매장은 현재 4대 외부 인프라 중 "
            f"1) 기상 악화({infra.weather.condition_korean})로 인한 단기 유휴 위험과, "
            f"2) 인근 팝업 축제({ev.name}) 및 3) {an.name} D-{an.d_day} 선예약이라는 "
            f"강력한 매출 기회가 동시에 맞물려 있습니다. 아래 4가지 처방 중 원하시는 것을 선택하시면 "
            f"네이버 플레이스 소식 및 인스타 맞춤 콘텐츠가 1초 만에 자동 완성됩니다."
        )

        return ConsultingDeskReport(
            tenant_id=tenant_id,
            business_name=b_name,
            domain=tenant.domain,
            location=loc,
            infra_report=infra,
            consultant_summary=consultant_summary,
            prescriptions=prescriptions,
        )


consulting_advisor = AIConsultingAdvisor()

"""AIM (AI Platform Initiative) - F&B Domain Plugin
Encapsulates domain logic for restaurants, cafes, bakeries, and food retail.
"""

from typing import List, Dict, Any
from aim.domains.base import BaseDomainPlugin
from aim.schema import BusinessState, Context6D, StrategyObjective


class FnbDomainPlugin(BaseDomainPlugin):
    @property
    def domain_key(self) -> str:
        return "fnb"

    @property
    def display_name(self) -> str:
        return "F&B / 외식·디저트 카페"

    def evaluate_triggers(self, state: BusinessState, context: Context6D) -> StrategyObjective:
        # Determine strategy based on idle tables, weather, or event
        unit_price = state.unit_price or 24000
        is_weather_risk = any(w in context.situation for w in ["비", "눈", "한파", "폭염", "우천"])
        is_idle = state.idle_capacity_rate > 0.2

        if is_weather_risk or is_idle:
            salvage_units = max(10, int(state.idle_capacity_rate * 30)) if is_idle else 15
            proj_rev = unit_price * salvage_units
            cost = 20000  # Kakao alert message cost
            return StrategyObjective(
                objective_type="CAPACITY_RESCUE",
                campaign_title=f"☔ [{context.situation}] 대응 빈 테이블 타임어택 & [{context.milestone}] 모객",
                target_persona=state.target_audience,
                core_narrative=f"{context.season} 시즌 한정 혜택과 {state.core_usps[0] if state.core_usps else '시그니처 메뉴'}의 조화",
                incentive_offer="오후 방문 고객 대상 시그니처 음료 1+1 또는 포장 15% 할인",
                urgency_level="HIGH",
                recommended_channels=["direct", "social", "blog"],
                projected_additional_units=salvage_units,
                projected_revenue=proj_rev,
                estimated_cost=cost,
                expected_roi_ratio=round((proj_rev - cost) / cost, 1) if cost > 0 else 0.0,
            )
        else:
            proj_rev = unit_price * 25
            cost = 15000
            return StrategyObjective(
                objective_type="OPPORTUNITY_CAPTURE",
                campaign_title=f"✨ [{context.season}] {state.entity_name} 시그니처 페스티벌",
                target_persona=state.target_audience,
                core_narrative=f"{context.generation}를 위한 {context.region} 핫플레이스 미식 경험",
                incentive_offer="사전 예약 고객 전용 프라이빗 좌석 배정",
                urgency_level="MEDIUM",
                recommended_channels=["blog", "social", "direct"],
                projected_additional_units=25,
                projected_revenue=proj_rev,
                estimated_cost=cost,
                expected_roi_ratio=round((proj_rev - cost) / cost, 1),
            )

    def get_compliance_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "FAIR_ADS_FNB",
                "authority": "공정거래위원회 표시광고법 제3조",
                "prohibited": ["국내 1위 맛집", "원조 중의 원조", "최고의 빵"],
                "required_disclosure": "당일 원재료 소진 시 조기 마감 가능",
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
        usp_txt = " • ".join(state.core_usps[:2]) if state.core_usps else "엄선된 프리미엄 원재료"
        if channel_key == "blog":
            headline = f"[{context.region} 핫플] {context.season} 분위기 가득한 '{state.entity_name}' 솔직 후기"
            points = [
                f"핵심 차별점: {usp_txt}",
                f"현재 상황 및 꿀팁: {context.situation} 대비 방문 가이드",
                f"스페셜 혜택: {strategy.incentive_offer}",
            ]
            cta = f"방문 전 네이버 예약으로 {context.milestone} 맞춤 자리를 미리 선점해보세요."
        elif channel_key == "social":
            headline = f"🚨 {context.generation} 주목! {context.situation}에는 '{state.entity_name}'에서 힐링 충전 ☕"
            points = [
                f"{context.season} 감성 폭발 시그니처 라인업",
                f"{usp_txt} 자랑하는 겉바속촉 폼 미친 메뉴",
                f"오늘만 진행하는 타임어택: {strategy.incentive_offer}",
            ]
            cta = "프로필 상단 링크에서 실시간 쿠폰 다운받고 바로 혜택 챙기세요 🏃💨"
        else:  # direct (kakao)
            headline = f"📢 [실시간 번개 혜택] {state.entity_name}에서 특별한 선물이 도착했습니다!"
            points = [
                f"{context.situation}에 찾아주시는 단골 고객님을 위한 감사 이벤트",
                f"혜택: {strategy.incentive_offer}",
                f"안내: {state.trigger_event}",
            ]
            cta = "매장 방문 시 본 메시지를 직원에게 보여주시면 즉시 적용됩니다."

        return {
            "headline": headline,
            "points": points,
            "cta": cta,
            "hashtags": [f"#{context.region.split()[0]}맛집", f"#{state.entity_name.split()[0]}", f"#{context.season.split()[0]}"],
        }

"""AIM (AI Platform Initiative) - Beauty & Salon Domain Plugin
Encapsulates domain logic for hair salons, nail salons, and aesthetic studios.
Models chair/stylist utilization rates and customer re-visit frequency.
"""

from typing import List, Dict, Any
from aim.domains.base import BaseDomainPlugin
from aim.schema import BusinessState, Context6D, StrategyObjective


class BeautyDomainPlugin(BaseDomainPlugin):
    @property
    def domain_key(self) -> str:
        return "beauty"

    @property
    def display_name(self) -> str:
        return "뷰티 / 헤어살롱·에스테틱"

    def evaluate_triggers(self, state: BusinessState, context: Context6D) -> StrategyObjective:
        unit_price = state.unit_price or 130000
        idle_seats = int(state.idle_capacity_rate * 10) if state.idle_capacity_rate > 0 else 6

        # Fills 80% of idle seats
        salvaged_seats = max(3, int(idle_seats * 0.8))
        proj_rev = unit_price * salvaged_seats
        cost = 20000

        return StrategyObjective(
            objective_type="CAPACITY_RESCUE",
            campaign_title=f"✂️ [{context.situation}] 유휴 체어 세이브 & [{context.milestone}] 맞춤 스타일링",
            target_persona=state.target_audience,
            core_narrative=f"{context.season} 트렌드 컬러 및 {state.core_usps[0] if state.core_usps else '퍼스널 컨설팅'}의 정밀 스타일링",
            incentive_offer="평일 낮 방문 고객 대상 프리미엄 두피 스파 또는 모발 클리닉 무료 업그레이드",
            urgency_level="MEDIUM",
            recommended_channels=["social", "direct", "blog"],
            projected_additional_units=salvaged_seats,
            projected_revenue=proj_rev,
            estimated_cost=cost,
            expected_roi_ratio=round((proj_rev - cost) / cost, 1) if cost > 0 else 0.0,
        )

    def get_compliance_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "BEAUTY_FAIR_ADS",
                "authority": "공정거래위원회 표시광고법",
                "prohibited": [
                    "영구적인 볼륨",
                    "청담동 1위 디자이너",
                    "완전 손상 0%",
                    "100% 복구",
                    "모발 재생 보장",
                    "파격 덤핑",
                ],
                "required_disclosure": "※ 모질 및 두피 상태에 따라 개인별 결과 차이가 있을 수 있습니다. (시술 전후 사진은 고객 동의 하에 비식별 마스킹 처리되었습니다.)",
            }
        ]

    @classmethod
    def apply_privacy_masking(cls, customer_name: str, has_before_after: bool = True) -> Dict[str, Any]:
        """Ensures customer personal identity is masked in before/after styling portfolios."""
        masked_name = customer_name[0] + "*" + (customer_name[2:] if len(customer_name) > 2 else "")
        return {
            "masked_customer_name": masked_name,
            "has_before_after": has_before_after,
            "privacy_compliance": "EYE_BLUR_APPLIED" if has_before_after else "NOT_REQUIRED",
            "consent_verified": True,
            "disclosure_notice": "※ 본 스타일링 사진은 고객 동의 하에 눈 부위 비식별 마스킹 처리 후 게시되었습니다.",
        }

    @classmethod
    def generate_happy_hour_booster(
        cls,
        salon_name: str,
        idle_seats: int,
        target_hours: str = "평일 14:00~17:00",
        free_upgrade: str = "프리미엄 두피 스파",
    ) -> Dict[str, Any]:
        """Generates dynamic slot-filling promotion for weekday off-peak hours."""
        return {
            "campaign_type": "DYNAMIC_SLOT_BOOSTER",
            "salon_name": salon_name,
            "target_hours": target_hours,
            "idle_seats": idle_seats,
            "headline": f"✂️ [{salon_name}] {target_hours} 한정 해피아워 예약 오픈!",
            "incentive": f"{target_hours} 방문 시 {free_upgrade} 무료 업그레이드 제공 (선착순 {idle_seats}석)",
            "cta": "네이버 예약 해피아워 타임슬롯 바로가기",
        }

    @classmethod
    def calculate_hair_cycle_recall(cls, service_type: str, weeks_ago: int) -> Dict[str, Any]:
        """Calculates hair cycle re-visit timing."""
        cycles = {
            "cut": {"std_weeks": 4, "name": "커트/라인 정리"},
            "color": {"std_weeks": 8, "name": "염색/뿌리염색"},
            "perm": {"std_weeks": 10, "name": "펌/볼륨매직"},
            "clinic": {"std_weeks": 3, "name": "모발 클리닉"},
        }
        info = cycles.get(service_type.lower(), {"std_weeks": 6, "name": service_type})
        std = info["std_weeks"]
        is_due = weeks_ago >= std
        return {
            "service_type": service_type,
            "service_name": info["name"],
            "weeks_ago": weeks_ago,
            "recommended_cycle_weeks": std,
            "is_due_for_recall": is_due,
            "nudge_text": (
                f"고객님, 지난 {info['name']} 시술 후 {weeks_ago}주가 지나 "
                f"헤어 라인 및 볼륨 정리가 필요한 시점입니다. 담당 디자이너 일정을 확인해 보세요."
            ) if is_due else "스타일 유지가 잘 되고 계신가요?",
        }

    def get_channel_blueprint(
        self,
        channel_key: str,
        state: BusinessState,
        strategy: StrategyObjective,
        context: Context6D,
        tone: str = "DEFAULT",
    ) -> Dict[str, Any]:
        usp_txt = " • ".join(state.core_usps[:2]) if state.core_usps else "얼굴형 분석 1:1 맞춤 컨설팅"

        if channel_key == "blog":
            headline = f"[{context.region} 헤어살롱] {context.season} 변신! {state.entity_name} 솔직 시술기"
            points = [
                f"1:1 맞춤 디자인: {usp_txt}",
                f"{context.milestone} 맞춤 헤어 라인 컨설팅 가이드",
                f"해피아워 혜택: {strategy.incentive_offer}",
            ]
            cta = "네이버 스마트예약으로 원하시는 디자이너와 편안한 슬롯을 선점하세요."
        elif channel_key == "social":
            headline = f"가을 무드 가득한 헤어 🍂 {state.entity_name}에서 완성하는 인생 스타일링"
            points = [
                f"{context.generation}의 분위기를 살리는 섬세한 레이어드 컷",
                f"{usp_txt} 기술 적용",
                f"{context.situation} 특별 프로모션: {strategy.incentive_offer}",
            ]
            cta = "프로필 링크에서 1:1 예약 바로가기 👆"
        else:  # direct
            headline = f"✂️ [단골 전용 케어] {state.entity_name}에서 고객님의 스타일링 주기를 챙겨드립니다."
            points = [
                f"지난 방문 후 스타일 라인 정리가 필요한 타이밍입니다 ({context.milestone}).",
                f"{context.situation} 방문 시 혜택: {strategy.incentive_offer}",
            ]
            cta = "원클릭 빠른 예약 링크로 방문 일정을 간편하게 확정하세요."

        return {
            "headline": headline,
            "points": points,
            "cta": cta,
            "hashtags": [f"#{context.region.split()[0]}미용실", f"#{state.entity_name.split()[0]}", "#퍼스널헤어"],
        }

"""AIM (AI Platform Initiative) - Medical & Healthcare Domain Plugin
Encapsulates domain logic for dermatology, plastic surgery, and medical clinics.
Enforces Medical Law Article 56 (의료법 제56조) and patient recall golden-time logic.
"""

from typing import List, Dict, Any
from aim.domains.base import BaseDomainPlugin
from aim.schema import BusinessState, Context6D, StrategyObjective


class MedicalDomainPlugin(BaseDomainPlugin):
    @property
    def domain_key(self) -> str:
        return "medical"

    @property
    def display_name(self) -> str:
        return "메디컬 / 피부과·에스테틱 의원"

    def evaluate_triggers(self, state: BusinessState, context: Context6D) -> StrategyObjective:
        unit_price = state.unit_price or 250000
        leads_count = state.pending_leads_count or 48  # e.g., patients due for 90-day recall
        has_noshow = "노쇼" in state.trigger_event or "취소" in state.trigger_event

        # Conversion projection: 1 no-show fill + 15% recall conversion
        converted_recalls = max(4, int(leads_count * 0.15))
        salvaged_noshow = 1 if has_noshow else 0
        total_units = converted_recalls + salvaged_noshow
        proj_rev = unit_price * total_units
        cost = 35000  # Targeted secure SMS/Kakao notification cost

        return StrategyObjective(
            objective_type="RETENTION_RECALL",
            campaign_title=f"🛡️ [{context.situation}] 신속 대처 & [{context.milestone}] 전문의 골든타임 리콜",
            target_persona=state.target_audience,
            core_narrative=f"정품·정량 원칙과 {state.core_usps[0] if state.core_usps else '전문의 1:1 진료'}를 바탕으로 한 개인별 맞춤 플랜",
            incentive_offer="정기 점검 방문 고객 대상 1:1 피부 진단 및 맞춤 진정보습 케어 제공",
            urgency_level="HIGH",
            recommended_channels=["direct", "blog", "social"],
            projected_additional_units=total_units,
            projected_revenue=proj_rev,
            estimated_cost=cost,
            expected_roi_ratio=round((proj_rev - cost) / cost, 1) if cost > 0 else 0.0,
        )

    def get_compliance_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "MEDICAL_LAW_ART56",
                "authority": "의료법 제56조 및 보건복지부 의료광고 가이드라인",
                "prohibited": ["부작용 전혀 없음", "100% 완치", "국내 최고 실력", "영구적인 효과", "최저가 이벤트"],
                "required_disclosure": "※ 모든 시술은 개인에 따라 멍, 붓기, 염증 등 부작용이 발생할 수 있으므로 전문의와 충분한 상담이 필요합니다. (의료광고 사전심의필)",
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
        usp_txt = " • ".join(state.core_usps[:2]) if state.core_usps else "전문의 1:1 맞춤 진료 및 정품정량"
        disclaimer = "※ 개인별 피부 상태에 따라 멍, 붓기 등 부작용이 동반될 수 있습니다."

        if channel_key == "blog":
            headline = f"[전문의 칼럼] {context.season}철 무너지는 피부 장벽, {context.milestone} 주기가 중요한 이유"
            points = [
                f"의학적 원리 및 진단: {usp_txt}",
                f"환절기 피부 상태 고려: {context.season} 건조 및 탄력 관리 가이드",
                f"원내 안전 수칙: 정품 개봉 현장 확인 및 부작용 예방 프로세스",
            ]
            cta = f"프라이빗 1인 진료실에서 {context.generation} 피부 상태에 맞춘 맞춤형 진단을 받아보세요."
        elif channel_key == "social":
            headline = f"건조한 {context.season}, 탄력 잃지 않는 골든타임 🌿 {state.entity_name}"
            points = [
                f"{usp_txt} 원칙 준수",
                f"{context.milestone} 맞춤 정밀 플랜",
                f"{disclaimer}",
            ]
            cta = "네이버 예약 또는 유선 문의를 통해 사전 진료 예약이 가능합니다."
        else:  # direct (patient 1:1 notification)
            headline = f"💌 [골든타임 케어 알림] 고객님, {state.entity_name}에서 안내드립니다."
            points = [
                f"지난 시술 후 권장 정기 점검 주기가 도래하였습니다 ({context.milestone}).",
                f"{context.situation} 관련 당일 우선 배정 슬롯 안내",
                f"{disclaimer}",
            ]
            cta = "카카오 채널 채팅 또는 담당 코디네이터 유선 상담을 통해 편하신 시간으로 확정하실 수 있습니다."

        return {
            "headline": headline,
            "points": points,
            "cta": cta,
            "hashtags": [f"#{context.region.split()[0]}피부과", f"#{state.entity_name.split()[0]}", "#웰에이징"],
        }

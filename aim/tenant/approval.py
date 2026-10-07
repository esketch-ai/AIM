"""AIM (AI Platform Initiative) - Tenant Approval Desk & Campaign Lifecycle
Manages staged campaigns, business owner review & one-click approval workflows,
and lifecycle state machine transitions (STAGED -> APPROVED -> DISPATCHED -> CONVERTED).
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from aim.schema import PlatformMarketingPlan, EvidenceTier
from aim.core.platform import AIMPlatform
from aim.tenant.manager import TenantManager
from aim.tenant.billing import BillingService


class StagedCampaign(BaseModel):
    campaign_id: str
    tenant_id: str
    business_name: str
    domain: str
    staged_at: str
    trigger_event: str
    urgency_level: str
    campaign_title: str
    objective_type: str
    target_persona: str
    recommended_channels: List[str]
    preview_copies: Dict[str, str]  # channel_key -> copy text preview
    all_compliant: bool
    compliance_summary: str
    projected_additional_units: int
    projected_revenue_krw: int
    status: str = Field(
        default="STAGED",
        description="'STAGED' (waiting for owner approval), 'APPROVED', 'REJECTED', 'EXPIRED'",
    )
    approved_at: Optional[str] = None
    executed_channels: List[str] = Field(default_factory=list)
    attribution_id: Optional[str] = None


class ApprovalDesk:
    """Manages staged campaign desk for business owners to review and authorize dispatches."""

    _staged_campaigns: Dict[str, StagedCampaign] = {}

    @classmethod
    def _initialize_defaults(cls) -> None:
        if cls._staged_campaigns:
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Seed initial staged campaigns for demonstration across tenants
        cls._staged_campaigns = {
            "CAMP-001": StagedCampaign(
                campaign_id="CAMP-001",
                tenant_id="TENANT_001",
                business_name="성수 아뜰리에 베이커리 & 카페",
                domain="fnb",
                staged_at=now_str,
                trigger_event="오늘 오후 15시 비 예보 + 2시 이후 사워도우 조기 품절",
                urgency_level="HIGH",
                campaign_title="☔ 가을비 타임어택 & 갓 구운 사워도우 사전 예약",
                objective_type="CAPACITY_RESCUE",
                target_persona="2030 MZ세대 및 비 오는 날 성수동 카페 방문객",
                recommended_channels=["blog", "social", "direct"],
                preview_copies={
                    "blog": "비 오는 날, 따뜻한 프랑스 AOP 버터 사워도우와 오트라떼 1+1 혜택을 사전 예약하세요.",
                    "social": "☔ 성수 비 예보 타임어택! 갓 구운 천연발효 빵과 테라스 우선 좌석 선착순 마감.",
                    "direct": "[성수 아뜰리에] 오늘 비 예보 특별 혜택! 사전 예약 고객 대상 웰컴 음료 증정.",
                },
                all_compliant=True,
                compliance_summary="공정위 표시광고법 제3조 사전 감사 100% 통과",
                projected_additional_units=10,
                projected_revenue_krw=240000,
                status="STAGED",
            ),
            "CAMP-002": StagedCampaign(
                campaign_id="CAMP-002",
                tenant_id="TENANT_002",
                business_name="강남 리엔 피부과의원",
                domain="medical",
                staged_at=now_str,
                trigger_event="오늘 16:30 원장 시술 예약 노쇼 1건 발생 + 보톡스 리콜 48명",
                urgency_level="CRITICAL",
                campaign_title="🏥 [긴급 노쇼 슬롯] 당일 프라이빗 1:1 맞춤 안티에이징 리콜",
                objective_type="CAPACITY_RESCUE",
                target_persona="2545 직장인 여성 및 주기 도래 고객",
                recommended_channels=["direct", "blog"],
                preview_copies={
                    "blog": "강남 리엔 피부과 전문의 1:1 진단과 정품 정량 시술로 환절기 피부 탄력을 회복하세요.",
                    "direct": "[리엔 피부과] 오늘 16:30 잔여 프라이빗 슬롯 긴급 안내 (부작용 가능성 사전 고지 및 심의필)",
                },
                all_compliant=True,
                compliance_summary="의료법 제56조 100% 필터링 (심의필 및 부작용 주의 문구 포함)",
                projected_additional_units=6,
                projected_revenue_krw=1500000,
                status="STAGED",
            ),
        }

    @classmethod
    def list_campaigns(
        cls, tenant_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[StagedCampaign]:
        cls._initialize_defaults()
        results = list(cls._staged_campaigns.values())
        if tenant_id:
            results = [c for c in results if c.tenant_id == tenant_id]
        if status:
            results = [c for c in results if c.status == status]
        return results

    @classmethod
    def get_campaign(cls, campaign_id: str) -> Optional[StagedCampaign]:
        cls._initialize_defaults()
        return cls._staged_campaigns.get(campaign_id)

    @classmethod
    def stage_new_campaign(
        cls, tenant_id: str, custom_trigger: Optional[str] = None
    ) -> StagedCampaign:
        """Generates a fresh AI campaign from tenant state and places it in the approval desk."""
        cls._initialize_defaults()
        tenant = TenantManager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant '{tenant_id}' not found")

        state = tenant.business_state
        if custom_trigger:
            state.trigger_event = custom_trigger

        plan = AIMPlatform.plan_campaign(state)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = len(cls._staged_campaigns) + 1
        camp_id = f"CAMP-{count:03d}"

        preview_copies = {
            k: (v.body[:150] + "..." if len(v.body) > 150 else v.body)
            for k, v in plan.channels.items()
        }

        staged = StagedCampaign(
            campaign_id=camp_id,
            tenant_id=tenant_id,
            business_name=tenant.business_name,
            domain=tenant.domain,
            staged_at=now_str,
            trigger_event=state.trigger_event,
            urgency_level=plan.strategy.urgency_level,
            campaign_title=plan.strategy.campaign_title,
            objective_type=plan.strategy.objective_type,
            target_persona=plan.strategy.target_persona,
            recommended_channels=plan.strategy.recommended_channels,
            preview_copies=preview_copies,
            all_compliant=plan.all_compliant,
            compliance_summary="✅ 100% 컴플라이언스 사전 필터링 통과" if plan.all_compliant else "⚠️ 검토 요망",
            projected_additional_units=plan.strategy.projected_additional_units,
            projected_revenue_krw=plan.strategy.projected_revenue,
            status="STAGED",
        )
        cls._staged_campaigns[camp_id] = staged
        return staged

    @classmethod
    def approve_and_dispatch(
        cls, campaign_id: str, selected_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Business owner authorizes the campaign. Dispatches to channels, updates ledger & revenue."""
        cls._initialize_defaults()
        camp = cls._staged_campaigns.get(campaign_id)
        if not camp:
            raise ValueError(f"Campaign '{campaign_id}' not found")
        if camp.status == "APPROVED":
            raise ValueError(f"Campaign '{campaign_id}' is already approved and executed")

        tenant = TenantManager.get_tenant(camp.tenant_id)
        if not tenant:
            raise ValueError(f"Tenant '{camp.tenant_id}' not found")

        # Plan and execute delivery
        plan = AIMPlatform.plan_campaign(tenant.business_state)
        channels = selected_channels or camp.recommended_channels
        exec_result = AIMPlatform.execute_campaign(plan, channels)

        # Update revenue on tenant account
        projected_rev = camp.projected_revenue_krw
        TenantManager.record_campaign_execution(camp.tenant_id, projected_rev)

        # Write to billing ROI attribution ledger
        attr_record = BillingService.record_attribution(
            tenant_id=camp.tenant_id,
            campaign_name=camp.campaign_title,
            revenue=projected_rev,
            monthly_fee=tenant.monthly_fee_krw,
            description=f"승인 데스크 원클릭 집행: {len(channels)}개 채널 동시 사출 완료",
        )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        camp.status = "APPROVED"
        camp.approved_at = now_str
        camp.executed_channels = channels
        camp.attribution_id = attr_record.record_id

        return {
            "status": "SUCCESS",
            "campaign_id": campaign_id,
            "tenant_id": camp.tenant_id,
            "business_name": camp.business_name,
            "dispatched_channels": channels,
            "projected_revenue": projected_rev,
            "attribution_record": attr_record.model_dump(),
            "evidence_tier": EvidenceTier.C_ILLUSTRATIVE.value,
            "message": f"'{camp.campaign_title}' 캠페인이 성공적으로 {len(channels)}개 채널에 송출되었습니다.",
        }

    @classmethod
    def reject_campaign(cls, campaign_id: str, reason: str = "") -> StagedCampaign:
        """Owner dismisses staged campaign recommendation."""
        cls._initialize_defaults()
        camp = cls._staged_campaigns.get(campaign_id)
        if not camp:
            raise ValueError(f"Campaign '{campaign_id}' not found")
        camp.status = "REJECTED"
        return camp

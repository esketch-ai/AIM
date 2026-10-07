"""AIM (AI Platform Initiative) - Tenant Billing & Value Attribution Service
Handles multi-tenant subscription tiers, invoicing schedules, and WTP (Willingness to Pay) ROI attribution.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TierFeature(BaseModel):
    name: str
    monthly_fee_krw: int
    max_stores: int
    allowed_channels: List[str]
    compliance_sla: str
    features: List[str]


TIER_CATALOG: Dict[str, TierFeature] = {
    "FREE": TierFeature(
        name="Free Explorer",
        monthly_fee_krw=0,
        max_stores=1,
        allowed_channels=["naver_blog"],
        compliance_sla="Standard (Batch)",
        features=["1개 매장 연동", "단일 채널 수동 발행", "기본 템플릿 제공"],
    ),
    "PRO": TierFeature(
        name="Pro Growth",
        monthly_fee_krw=49000,
        max_stores=3,
        allowed_channels=["naver_blog", "instagram", "kakaotalk"],
        compliance_sla="Real-time (3ms)",
        features=[
            "최대 3개 매장/지점 통합 관리",
            "3대 옴니채널 원클릭 즉시 발송",
            "실시간 6D 컨텍스트 감지 (날씨/유휴/기념일)",
            "공정위·의료법 100% 사전 컴플라이언스 필터",
            "구독료 대비 매출 정산 리포트",
        ],
    ),
    "ENTERPRISE": TierFeature(
        name="Enterprise Dominance",
        monthly_fee_krw=199000,
        max_stores=999,
        allowed_channels=["naver_blog", "instagram", "kakaotalk", "b2b_rfq", "email_dispatch"],
        compliance_sla="Dedicated High-Priority (1ms + Legal Review)",
        features=[
            "전국 무제한 직영/가맹점 통합 관제",
            "의료법/광고법/GDPR 커스텀 법무 가드레일",
            "B2B RFQ 영문 무역 공문 & 글로벌 발송",
            "전담 플랫폼 디렉터 1:1 배정 & SLA 99.99%",
            "ERP / POS 실측 정산 API 양방향 동기화",
        ],
    ),
}


class Invoice(BaseModel):
    invoice_id: str
    tenant_id: str
    billing_period: str
    tier: str
    amount_krw: int
    status: str = Field(default="PAID", description="'PAID', 'PENDING', 'FAILED'")
    issued_at: str
    paid_at: Optional[str] = None
    payment_method: str = "신용카드 자동결제 (빌링키)"


class AttributionRecord(BaseModel):
    record_id: str
    tenant_id: str
    campaign_name: str
    executed_at: str
    generated_revenue_krw: int
    monthly_fee_krw: int
    net_value_krw: int
    roi_multiplier: float
    description: str


class BillingService:
    """Manages subscription tier catalog, tenant invoices, and ROI attribution ledger."""

    _invoices: Dict[str, List[Invoice]] = {}
    _attributions: Dict[str, List[AttributionRecord]] = {}

    @classmethod
    def _initialize_defaults(cls) -> None:
        if cls._invoices:
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Initial seed invoices for demo tenants
        cls._invoices = {
            "TENANT_001": [
                Invoice(
                    invoice_id="INV-202610-001",
                    tenant_id="TENANT_001",
                    billing_period="2026-10",
                    tier="PRO",
                    amount_krw=49000,
                    status="PAID",
                    issued_at="2026-10-01 00:00:00",
                    paid_at="2026-10-01 00:00:05",
                ),
                Invoice(
                    invoice_id="INV-202609-001",
                    tenant_id="TENANT_001",
                    billing_period="2026-09",
                    tier="PRO",
                    amount_krw=49000,
                    status="PAID",
                    issued_at="2026-09-01 00:00:00",
                    paid_at="2026-09-01 00:00:05",
                ),
            ],
            "TENANT_002": [
                Invoice(
                    invoice_id="INV-202610-002",
                    tenant_id="TENANT_002",
                    billing_period="2026-10",
                    tier="ENTERPRISE",
                    amount_krw=199000,
                    status="PAID",
                    issued_at="2026-10-01 00:00:00",
                    paid_at="2026-10-01 00:00:03",
                ),
            ],
            "TENANT_003": [
                Invoice(
                    invoice_id="INV-202610-003",
                    tenant_id="TENANT_003",
                    billing_period="2026-10",
                    tier="PRO",
                    amount_krw=49000,
                    status="PAID",
                    issued_at="2026-10-01 00:00:00",
                    paid_at="2026-10-01 00:00:04",
                ),
            ],
            "TENANT_004": [
                Invoice(
                    invoice_id="INV-202610-004",
                    tenant_id="TENANT_004",
                    billing_period="2026-10",
                    tier="PRO",
                    amount_krw=49000,
                    status="PAID",
                    issued_at="2026-10-01 00:00:00",
                    paid_at="2026-10-01 00:00:06",
                ),
            ],
            "TENANT_005": [
                Invoice(
                    invoice_id="INV-202610-005",
                    tenant_id="TENANT_005",
                    billing_period="2026-10",
                    tier="ENTERPRISE",
                    amount_krw=199000,
                    status="PAID",
                    issued_at="2026-10-01 00:00:00",
                    paid_at="2026-10-01 00:00:02",
                ),
            ],
        }

        # Seed attribution records
        cls._attributions = {
            "TENANT_001": [
                AttributionRecord(
                    record_id="ATTR-001",
                    tenant_id="TENANT_001",
                    campaign_name="우천 예보 사워도우 사전 예약 타임어택",
                    executed_at="2026-10-07 14:00:00",
                    generated_revenue_krw=360000,
                    monthly_fee_krw=49000,
                    net_value_krw=311000,
                    roi_multiplier=7.3,
                    description="15개 유휴 테이블 조기 만석 유치 (객단가 24,000원)",
                )
            ],
            "TENANT_002": [
                AttributionRecord(
                    record_id="ATTR-002",
                    tenant_id="TENANT_002",
                    campaign_name="노쇼 슬롯 긴급 리프팅 리콜",
                    executed_at="2026-10-07 14:15:00",
                    generated_revenue_krw=1500000,
                    monthly_fee_krw=199000,
                    net_value_krw=1301000,
                    roi_multiplier=7.5,
                    description="원장 공백 슬롯 6건 즉시 예약 전환 (객단가 250,000원)",
                )
            ],
        }

    @classmethod
    def get_tier_catalog(cls) -> Dict[str, TierFeature]:
        return TIER_CATALOG

    @classmethod
    def get_tier_info(cls, tier: str) -> Optional[TierFeature]:
        return TIER_CATALOG.get(tier.upper())

    @classmethod
    def get_tenant_invoices(cls, tenant_id: str) -> List[Invoice]:
        cls._initialize_defaults()
        return cls._invoices.get(tenant_id, [])

    @classmethod
    def create_invoice(
        cls, tenant_id: str, tier: str, period: Optional[str] = None
    ) -> Invoice:
        cls._initialize_defaults()
        tier_info = cls.get_tier_info(tier)
        amount = tier_info.monthly_fee_krw if tier_info else 0
        current_period = period or datetime.now().strftime("%Y-%m")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        count = sum(len(invs) for invs in cls._invoices.values()) + 1
        new_inv = Invoice(
            invoice_id=f"INV-{current_period.replace('-', '')}-{count:03d}",
            tenant_id=tenant_id,
            billing_period=current_period,
            tier=tier.upper(),
            amount_krw=amount,
            status="PAID",
            issued_at=now_str,
            paid_at=now_str,
        )
        if tenant_id not in cls._invoices:
            cls._invoices[tenant_id] = []
        cls._invoices[tenant_id].insert(0, new_inv)
        return new_inv

    @classmethod
    def record_attribution(
        cls,
        tenant_id: str,
        campaign_name: str,
        revenue: int,
        monthly_fee: int,
        description: str = "",
    ) -> AttributionRecord:
        cls._initialize_defaults()
        net_val = revenue - monthly_fee
        roi = round(revenue / monthly_fee, 1) if monthly_fee > 0 else 0.0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        count = sum(len(attrs) for attrs in cls._attributions.values()) + 1
        record = AttributionRecord(
            record_id=f"ATTR-{count:03d}",
            tenant_id=tenant_id,
            campaign_name=campaign_name,
            executed_at=now_str,
            generated_revenue_krw=revenue,
            monthly_fee_krw=monthly_fee,
            net_value_krw=net_val,
            roi_multiplier=roi,
            description=description,
        )
        if tenant_id not in cls._attributions:
            cls._attributions[tenant_id] = []
        cls._attributions[tenant_id].insert(0, record)
        return record

    @classmethod
    def get_tenant_attributions(cls, tenant_id: str) -> List[AttributionRecord]:
        cls._initialize_defaults()
        return cls._attributions.get(tenant_id, [])

    @classmethod
    def get_financial_summary(cls, tenant_id: str, monthly_fee: int) -> Dict[str, Any]:
        cls._initialize_defaults()
        attrs = cls.get_tenant_attributions(tenant_id)
        total_attributed_revenue = sum(a.generated_revenue_krw for a in attrs)
        total_invoiced_fees = sum(
            inv.amount_krw for inv in cls.get_tenant_invoices(tenant_id) if inv.status == "PAID"
        )
        net_value_created = total_attributed_revenue - total_invoiced_fees
        overall_roi = (
            round(total_attributed_revenue / total_invoiced_fees, 1)
            if total_invoiced_fees > 0
            else 0.0
        )

        return {
            "tenant_id": tenant_id,
            "monthly_fee_krw": monthly_fee,
            "total_attributed_revenue_krw": total_attributed_revenue,
            "total_invoiced_fees_krw": total_invoiced_fees,
            "net_value_created_krw": net_value_created,
            "overall_roi_multiplier": overall_roi,
            "attribution_records_count": len(attrs),
        }

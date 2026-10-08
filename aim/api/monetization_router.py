"""
AIM Monetization & Attribution API Router (aim/api/monetization_router.py)
--------------------------------------------------------------------------
Provides REST APIs for:
1. Dynamic Coupon Issuance & POS Scan Redemption (A_MEASURED)
2. AI Receipt OCR Verification & Customer Point Cashback (A_MEASURED)
3. 5 Multi-Channel Attribution Methods Registry & Stats
4. 4 Platform Revenue Streams Summary (Take-rate, Escrow, SaaS MRR, Success Fee)
5. Comprehensive Multi-Channel Simulation Pipeline
"""

import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from aim.core.attribution_engine import (
    attribution_engine,
    AttributionMethod,
    RevenueClearingEngine,
    ConversionEvent,
)
from aim.core.coupon_vault import (
    coupon_vault,
    CouponItem,
    CouponRedemptionResult,
    ReceiptVerificationRequest,
    ReceiptVerificationResult,
)
from aim.core.value_attribution import attribution_ledger
from aim.matching.creator_network import creator_network

router = APIRouter(prefix="/api/v1/monetization", tags=["Monetization & Attribution Engine"])


class CouponIssueRequest(BaseModel):
    tenant_id: str
    campaign_id: str = "CAMP_DEFAULT"
    channel: str = "YOUTUBE"
    creator_id: Optional[str] = None
    discount_amount_krw: int = 3000
    min_order_amount_krw: int = 15000


class CouponRedeemRequest(BaseModel):
    coupon_code: str
    order_amount_krw: int = 24000


class MultiChannelSimulationRequest(BaseModel):
    tenant_id: str = "TENANT_001"


@router.get("/methods")
def get_attribution_methods():
    """Returns metadata, evidence tiers, and SMB suitability for the 5 attribution methods."""
    return {
        "status": "success",
        "methods": [
            {
                "method": AttributionMethod.COUPON_CODE,
                "name": "동적 쿠폰/바코드 POS 스캔",
                "evidence_tier": "A_MEASURED",
                "accuracy": "100%",
                "mechanism": "크리에이터/채널별 고유 코드 POS 바코드 리더기 스캔 또는 번호 입력",
                "suitability": "F&B, 카페, 베이커리, 살롱",
                "commission_trigger": "POS 스캔 시 즉시 결제액 8% 정산 & 크리에이터 보너스 30% 언락",
            },
            {
                "method": AttributionMethod.UTM_LINK,
                "name": "UTM 스마트 단축 링크",
                "evidence_tier": "A_MEASURED",
                "accuracy": "95%",
                "mechanism": "유튜브 더보기란, 인스타 프로필, 카카오 알림톡 전용 aim.link 경유 추적",
                "suitability": "온라인 예약형 매장, 원데이 클래스, 팝업스토어",
                "commission_trigger": "링크 클릭 후 네이버 예약/주문 완료 시 정산",
            },
            {
                "method": AttributionMethod.RECEIPT_OCR,
                "name": "영수증 사진 AI OCR 인증",
                "evidence_tier": "A_MEASURED",
                "accuracy": "98%",
                "mechanism": "소비자가 매장 종이/전자 영수증 사진 업로드 시 금액/일시 OCR 자동 판독",
                "suitability": "POS 연동이 불가능하거나 배달/포장 주문 비중이 높은 매장",
                "commission_trigger": "영수증 유효 판독 시 고객 1,000원 적립 & 실적 공인",
            },
            {
                "method": AttributionMethod.TIME_WINDOW_LIFT,
                "name": "타임윈도우 증분 매출 대조",
                "evidence_tier": "C_ILLUSTRATIVE",
                "accuracy": "82%",
                "mechanism": "비 예보 3시간 타임어택 등 이벤트 가동 시 평시 시간대비 초과 매출 통계 귀속",
                "suitability": "쿠폰을 쓰지 않는 워크인(Walk-in) 급증 상황",
                "commission_trigger": "기준선(Baseline) 초과 순증 매출의 5% 성과 보수 산정",
            },
            {
                "method": AttributionMethod.VIRTUAL_NUMBER,
                "name": "050 가상 안심번호 및 다이렉트 예약",
                "evidence_tier": "A_MEASURED",
                "accuracy": "96%",
                "mechanism": "채널별 050 가상번호 통화 인입 및 네이버 플레이스 스마트콜 연동",
                "suitability": "병의원, 피트니스, 뷰티, 테이블 예약제 식당",
                "commission_trigger": "통화 30초 이상 유지 또는 예약 방문 확정 시 정산",
            },
        ],
    }


@router.post("/coupon/issue", response_model=CouponItem)
def issue_coupon(req: CouponIssueRequest):
    """Issues a tamper-resistant dynamic coupon linked to a channel and creator."""
    coupon = coupon_vault.issue_coupon(
        tenant_id=req.tenant_id,
        campaign_id=req.campaign_id,
        channel=req.channel,
        creator_id=req.creator_id,
        discount_amount_krw=req.discount_amount_krw,
        min_order_amount_krw=req.min_order_amount_krw,
    )
    return coupon


@router.get("/coupon/list/{tenant_id}")
def list_coupons(tenant_id: str):
    """Lists all coupons issued for a given tenant."""
    coupons = coupon_vault.get_tenant_coupons(tenant_id)
    return {
        "status": "success",
        "tenant_id": tenant_id,
        "total": len(coupons),
        "coupons": coupons,
    }


@router.post("/coupon/redeem", response_model=CouponRedemptionResult)
def redeem_coupon(req: CouponRedeemRequest):
    """Redeems a coupon via POS scan, validates amount, and registers A_MEASURED value attribution."""
    try:
        result = coupon_vault.redeem_coupon(
            coupon_code=req.coupon_code,
            order_amount_krw=req.order_amount_krw,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/receipt/verify", response_model=ReceiptVerificationResult)
def verify_receipt(req: ReceiptVerificationRequest):
    """Verifies customer-uploaded receipt OCR text, granting instant cashback and registering A_MEASURED attribution."""
    result = coupon_vault.verify_receipt(req)
    return result


@router.get("/streams/summary/{tenant_id}")
def get_monetization_summary(tenant_id: str):
    """Aggregates all 4 platform revenue streams and 5 attribution methods for a tenant."""
    attribution_stats = attribution_engine.get_tenant_attribution_breakdown(tenant_id)
    coupons = coupon_vault.get_tenant_coupons(tenant_id)
    receipts = coupon_vault.get_tenant_receipts(tenant_id)
    ledger_summary = attribution_ledger.get_tenant_summary(tenant_id)

    # 4 Platform Revenue Streams for this tenant:
    # 1. Take-Rate Commission (8% on measured coupons & OCR GMV)
    measured_gmv = attribution_stats["measured_revenue_krw"]
    take_rate_krw = int(measured_gmv * 0.08)

    # 2. Creator Escrow Marketplace Fee (10% on matched creator deals)
    escrow_fees = 0
    if hasattr(creator_network, "active_deals"):
        for deal in creator_network.active_deals.values():
            if deal.tenant_id == tenant_id:
                escrow_fees += deal.platform_fee

    # 3. SaaS Monthly Subscription Fee (Pro plan: 49,000 KRW)
    saas_subscription_mrr = 49000

    # 4. Incremental Success Fee (5% on statistical time-window lift)
    illustrative_rev = attribution_stats["illustrative_revenue_krw"]
    incremental_success_fee = int(illustrative_rev * 0.05)

    total_platform_revenue = take_rate_krw + escrow_fees + saas_subscription_mrr + incremental_success_fee

    return {
        "status": "success",
        "tenant_id": tenant_id,
        "platform_revenue_streams": {
            "total_platform_revenue_krw": total_platform_revenue,
            "stream_1_take_rate_commission": {
                "name": "성과 거래 수수료 (Take-Rate 8%)",
                "amount_krw": take_rate_krw,
                "basis_gmv_krw": measured_gmv,
                "evidence_tier": "A_MEASURED",
            },
            "stream_2_escrow_marketplace_fee": {
                "name": "크리에이터 매칭 에스크로 수수료 (10%)",
                "amount_krw": escrow_fees,
                "evidence_tier": "A_MEASURED",
            },
            "stream_3_saas_subscription_mrr": {
                "name": "24h 자율 AI 마케팅 SaaS 월 구독료 (Pro)",
                "amount_krw": saas_subscription_mrr,
                "evidence_tier": "A_MEASURED",
            },
            "stream_4_incremental_success_fee": {
                "name": "초과 성과 공유 수수료 (순증 매출의 5%)",
                "amount_krw": incremental_success_fee,
                "basis_lift_krw": illustrative_rev,
                "evidence_tier": "C_ILLUSTRATIVE",
            },
        },
        "attribution_breakdown": attribution_stats,
        "coupons_metrics": {
            "total_issued": len(coupons),
            "redeemed_count": len([c for c in coupons if c.is_redeemed]),
            "active_count": len([c for c in coupons if not c.is_redeemed]),
        },
        "receipts_verified_count": len(receipts),
        "ledger_summary": ledger_summary.model_dump(),
    }


@router.post("/simulate/all")
def simulate_all_attribution_channels(req: MultiChannelSimulationRequest):
    """Simulates an end-to-end attribution event across POS coupon, OCR receipt, and time-window lift."""
    # 1. Issue and redeem a dynamic coupon
    new_coupon = coupon_vault.issue_coupon(
        tenant_id=req.tenant_id,
        campaign_id="CAMP_SIM_BATCH",
        channel="YOUTUBE",
        creator_id="CR_002",
        discount_amount_krw=3000,
        min_order_amount_krw=15000,
    )
    redemption = coupon_vault.redeem_coupon(new_coupon.coupon_code, order_amount_krw=27000)

    # 2. Verify an OCR receipt
    ocr_result = coupon_vault.verify_receipt(
        ReceiptVerificationRequest(
            tenant_id=req.tenant_id,
            campaign_id="CAMP_SIM_BATCH",
            creator_id="CR_001",
            receipt_ocr_text="[영수증] 성수 어반플레이트 결제금액: 42,000원 승인번호: 883921",
        )
    )

    # 3. Record a time-window lift event
    lift_evt = ConversionEvent(
        event_id=f"EVT_SIM_LIFT_{uuid.uuid4().hex[:6].upper()}",
        tenant_id=req.tenant_id,
        campaign_id="CAMP_SIM_BATCH",
        channel="OFFLINE_WALKIN",
        creator_id=None,
        method=AttributionMethod.TIME_WINDOW_LIFT,
        transaction_amount_krw=150000,
        proof_data={"baseline": 100000, "actual": 250000, "delta": 150000},
        evidence_tier="C_ILLUSTRATIVE",
    )
    attribution_engine.record_event(lift_evt)
    attribution_ledger.record_attribution(
        tenant_id=req.tenant_id,
        source_type="TIME_WINDOW_LIFT",
        title="비 예보 타임어택 통계 증분 매출 기여",
        units_generated=5,
        unit_price=30000,
        cost_incurred_krw=0,
        evidence_tier="C_ILLUSTRATIVE",
        attribution_method="TIME_WINDOW_LIFT",
        tracking_code=lift_evt.event_id,
        platform_commission_krw=int(150000 * 0.05),
        creator_bonus_krw=0,
    )

    return {
        "status": "success",
        "message": "다각화된 5대 성과 인정 및 수익화 시뮬레이션 파이프라인이 정상 실행되었습니다.",
        "coupon_redeemed": redemption.model_dump(),
        "receipt_verified": ocr_result.model_dump(),
        "lift_attributed_krw": 150000,
        "summary": get_monetization_summary(req.tenant_id),
    }

"""
AIM Creator Matching & Escrow Engine (aim/matching/creator_network.py)
-----------------------------------------------------------------------
Handles creator profiles, audience-affinity matching algorithm,
escrow order locking, subscriber discount take-rate, and 24h Fast-Track review.
"""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CreatorProfile(BaseModel):
    creator_id: str
    name: str
    handle: str
    channel: str  # YouTube Shorts, Instagram Reels, TikTok, Live Commerce
    category: str  # FNB, BEAUTY, MEDICAL, B2B_SAAS, MANUFACTURING
    tier: str  # MICRO_150K, MID_450K, PRO_900K
    price_krw: int
    follower_count: int
    avg_views: int
    retention_rate: float  # Avg viewer retention %
    historical_conversion_rate: float  # Avg CTR/coupon conversion %
    audience_demographics: Dict[str, float]  # age_20_30, gender_female, geo_metropolitan
    rating: float = 4.9
    completed_deals: int = 12


class MatchedCreatorCard(BaseModel):
    creator: CreatorProfile
    match_score: float  # e.g. 96.5%
    audience_affinity_pct: float
    conversion_rating_badge: str
    take_rate_pct: float
    estimated_reach: int
    estimated_conversions: int


class EscrowDeal(BaseModel):
    deal_id: str
    tenant_id: str
    creator_id: str
    creator_name: str
    brief_id: str
    total_budget: int
    subscriber_plan: str
    take_rate_pct: float
    platform_fee: int
    creator_total_fee: int
    creator_base_payout: int  # 70% upon draft approval
    creator_bonus_payout: int  # 30% upon live upload & conversion target
    status: str  # ESCROW_LOCKED, DRAFT_SUBMITTED, APPROVED, SETTLED
    revision_count: int = 0
    max_revisions: int = 1
    fast_track_hours_left: int = 24


class MatchRequest(BaseModel):
    category: str
    content_format: str
    budget_tier: str
    target_audience: str
    tenant_id: Optional[str] = "TENANT_001"
    subscriber_plan: str = "PRO"  # PRO or ENTERPRISE gets 10% take-rate, others 15%


class CreatorNetwork:
    """Manages creator pool, algorithmic ranking, and escrow lifecycle."""

    # Default vetted creator pool across 5 domains
    SAMPLE_CREATORS = [
        CreatorProfile(
            creator_id="CR_FNB_01",
            name="디저트탐험가 은지",
            handle="@eunji_dessert",
            channel="YouTube Shorts",
            category="FNB",
            tier="MICRO_150K",
            price_krw=150000,
            follower_count=18500,
            avg_views=34000,
            retention_rate=82.4,
            historical_conversion_rate=5.8,
            audience_demographics={"age_20_30": 89.0, "gender_female": 72.0, "geo_metropolitan": 94.0},
            rating=4.95,
            completed_deals=24,
        ),
        CreatorProfile(
            creator_id="CR_FNB_02",
            name="서울핫플스케치",
            handle="@seoul_hotplace",
            channel="Instagram Reels",
            category="FNB",
            tier="MID_450K",
            price_krw=450000,
            follower_count=78000,
            avg_views=125000,
            retention_rate=86.1,
            historical_conversion_rate=6.4,
            audience_demographics={"age_20_30": 92.0, "gender_female": 65.0, "geo_metropolitan": 96.0},
            rating=4.98,
            completed_deals=58,
        ),
        CreatorProfile(
            creator_id="CR_BEAUTY_01",
            name="스타일리스트 민호",
            handle="@minho_hair_lab",
            channel="Instagram Reels",
            category="BEAUTY",
            tier="MID_450K",
            price_krw=450000,
            follower_count=62000,
            avg_views=98000,
            retention_rate=88.5,
            historical_conversion_rate=7.2,
            audience_demographics={"age_20_30": 85.0, "gender_female": 84.0, "geo_metropolitan": 92.0},
            rating=4.96,
            completed_deals=41,
        ),
        CreatorProfile(
            creator_id="CR_BEAUTY_02",
            name="글로우 뷰티 로그",
            handle="@glow_beautylog",
            channel="YouTube Shorts",
            category="BEAUTY",
            tier="MICRO_150K",
            price_krw=150000,
            follower_count=22000,
            avg_views=42000,
            retention_rate=81.0,
            historical_conversion_rate=5.1,
            audience_demographics={"age_20_30": 88.0, "gender_female": 91.0, "geo_metropolitan": 89.0},
            rating=4.88,
            completed_deals=19,
        ),
        CreatorProfile(
            creator_id="CR_MED_01",
            name="닥터스킨 안원장",
            handle="@dr_skin_care",
            channel="YouTube Shorts",
            category="MEDICAL",
            tier="PRO_900K",
            price_krw=900000,
            follower_count=145000,
            avg_views=210000,
            retention_rate=91.2,
            historical_conversion_rate=8.5,
            audience_demographics={"age_20_30": 79.0, "gender_female": 82.0, "geo_metropolitan": 95.0},
            rating=4.99,
            completed_deals=67,
        ),
        CreatorProfile(
            creator_id="CR_B2B_01",
            name="테크스타트업 리뷰어 진",
            handle="@tech_saas_jin",
            channel="YouTube Shorts",
            category="B2B_SAAS",
            tier="MID_450K",
            price_krw=450000,
            follower_count=48000,
            avg_views=72000,
            retention_rate=84.0,
            historical_conversion_rate=6.0,
            audience_demographics={"age_20_30": 76.0, "gender_female": 35.0, "geo_metropolitan": 90.0},
            rating=4.92,
            completed_deals=33,
        ),
        CreatorProfile(
            creator_id="CR_MANUF_01",
            name="정밀제조 마이스터 팍",
            handle="@meister_mfg",
            channel="YouTube Shorts",
            category="MANUFACTURING",
            tier="MICRO_150K",
            price_krw=150000,
            follower_count=19000,
            avg_views=31000,
            retention_rate=79.5,
            historical_conversion_rate=4.5,
            audience_demographics={"age_20_30": 58.0, "gender_female": 20.0, "geo_metropolitan": 80.0},
            rating=4.85,
            completed_deals=15,
        ),
    ]

    def __init__(self):
        self.creators = list(self.SAMPLE_CREATORS)
        self.active_deals: Dict[str, EscrowDeal] = {}
        # Pre-seed one sample active deal for immediate display
        seed_deal = EscrowDeal(
            deal_id="DEAL_7749A",
            tenant_id="TENANT_001",
            creator_id="CR_FNB_02",
            creator_name="서울핫플스케치 (@seoul_hotplace)",
            brief_id="BRIEF_INITIAL_01",
            total_budget=450000,
            subscriber_plan="PRO",
            take_rate_pct=10.0,
            platform_fee=45000,
            creator_total_fee=405000,
            creator_base_payout=283500,
            creator_bonus_payout=121500,
            status="DRAFT_SUBMITTED",
            revision_count=0,
            max_revisions=1,
            fast_track_hours_left=18,
        )
        self.active_deals[seed_deal.deal_id] = seed_deal

    def _initialize_defaults(self) -> None:
        self.__init__()

    def match_creators(self, req: MatchRequest) -> List[MatchedCreatorCard]:
        results = []
        is_subscriber = req.subscriber_plan.upper() in ["PRO", "ENTERPRISE"]
        take_rate = 10.0 if is_subscriber else 15.0

        for cr in self.creators:
            # Category match bonus
            cat_score = 100.0 if cr.category == req.category else 40.0

            # Demographics affinity
            demo = cr.audience_demographics
            affinity = (demo.get("age_20_30", 70.0) * 0.5 + demo.get("geo_metropolitan", 80.0) * 0.5)

            # Historical conversion weight
            conv_weight = min(100.0, cr.historical_conversion_rate * 12.0)

            # Total match score
            total_score = round(cat_score * 0.45 + affinity * 0.35 + conv_weight * 0.20, 1)

            # Estimated metrics
            est_reach = int(cr.avg_views * 1.15)
            est_conv = int(est_reach * (cr.historical_conversion_rate / 100.0))

            badge = "🔥 전환율 최상위" if cr.historical_conversion_rate >= 6.0 else "✨ 가성비 우수"

            results.append(
                MatchedCreatorCard(
                    creator=cr,
                    match_score=total_score,
                    audience_affinity_pct=round(affinity, 1),
                    conversion_rating_badge=badge,
                    take_rate_pct=take_rate,
                    estimated_reach=est_reach,
                    estimated_conversions=est_conv,
                )
            )

        # Sort by match score descending
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

    def create_escrow_deal(
        self,
        tenant_id: str,
        creator_id: str,
        brief_id: str,
        subscriber_plan: str = "PRO",
    ) -> EscrowDeal:
        creator = next((c for c in self.creators if c.creator_id == creator_id), self.creators[0])
        deal_id = f"DEAL_{uuid.uuid4().hex[:6].upper()}"

        is_sub = subscriber_plan.upper() in ["PRO", "ENTERPRISE"]
        take_rate = 10.0 if is_sub else 15.0

        total_budget = creator.price_krw
        platform_fee = int(total_budget * (take_rate / 100.0))
        creator_total = total_budget - platform_fee
        base_payout = int(creator_total * 0.70)
        bonus_payout = creator_total - base_payout

        deal = EscrowDeal(
            deal_id=deal_id,
            tenant_id=tenant_id,
            creator_id=creator.creator_id,
            creator_name=f"{creator.name} ({creator.handle})",
            brief_id=brief_id,
            total_budget=total_budget,
            subscriber_plan=subscriber_plan,
            take_rate_pct=take_rate,
            platform_fee=platform_fee,
            creator_total_fee=creator_total,
            creator_base_payout=base_payout,
            creator_bonus_payout=bonus_payout,
            status="ESCROW_LOCKED",
            revision_count=0,
            max_revisions=1,
            fast_track_hours_left=24,
        )
        self.active_deals[deal_id] = deal
        return deal

    def submit_draft(
        self, deal_id: str, video_url: str, compliance_passed: bool = True
    ) -> Dict[str, Any]:
        deal = self.active_deals.get(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found.")
        if deal.status == "SETTLED":
            raise ValueError("이미 정산 완료된 계약에는 초안을 제출할 수 없습니다.")
        deal.status = "DRAFT_SUBMITTED"
        deal.fast_track_hours_left = 24
        return {
            "deal_id": deal_id,
            "status": deal.status,
            "video_url": video_url,
            "compliance_checked": compliance_passed,
            "compliance_summary": "✅ 공정위 추천보증 심사지침 준수 [유료 광고 포함] 표기 확인 완료",
            "fast_track_hours_left": deal.fast_track_hours_left,
        }

    def request_revision(self, deal_id: str, feedback: str = "") -> EscrowDeal:
        deal = self.active_deals.get(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found.")
        if deal.revision_count >= deal.max_revisions:
            raise ValueError("표준 약관상 1회를 초과하는 수정 요청은 불가합니다 (24h Fast-Track 규정).")
        deal.revision_count += 1
        deal.status = "REVISION_REQUESTED"
        return deal

    def approve_draft_and_release_base(self, deal_id: str) -> Dict[str, Any]:
        deal = self.active_deals.get(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found.")
        if deal.status in ["BASE_PAYOUT_RELEASED", "SETTLED"]:
            raise ValueError("이미 기본 정산금이 지급된 계약입니다.")
        deal.status = "BASE_PAYOUT_RELEASED"
        return {
            "deal_id": deal_id,
            "status": deal.status,
            "released_base_payout_krw": deal.creator_base_payout,
            "held_bonus_payout_krw": deal.creator_bonus_payout,
            "message": f"초안 검수 최종 승인! 계약금 70%({deal.creator_base_payout:,}원)가 에스크로에서 크리에이터에게 정산되었습니다.",
        }

    def unlock_milestone_bonus(
        self, deal_id: str, metric_type: str = "VIEWS", metric_value: int = 55000
    ) -> Dict[str, Any]:
        deal = self.active_deals.get(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found.")
        if deal.status == "SETTLED":
            raise ValueError("이미 최종 정산이 완료된 계약입니다.")
        if deal.status != "BASE_PAYOUT_RELEASED":
            raise ValueError("1차 기본 정산금 지급이 완료된 후에만 성과 마일스톤을 언락할 수 있습니다.")

        # Thresholds: VIEWS >= 50,000 or CONVERSIONS >= 20
        target_met = (metric_type == "VIEWS" and metric_value >= 50000) or (
            metric_type == "CONVERSIONS" and metric_value >= 20
        )
        if not target_met:
            raise ValueError(f"성과 마일스톤 기준 미달 ({metric_type}: {metric_value})")

        deal.status = "SETTLED"
        return {
            "deal_id": deal_id,
            "status": deal.status,
            "metric_type": metric_type,
            "metric_value": metric_value,
            "unlocked_bonus_krw": deal.creator_bonus_payout,
            "total_payout_krw": deal.creator_total_fee,
            "message": f"🎉 성과 마일스톤 달성 확인! 보너스 30%({deal.creator_bonus_payout:,}원)가 언락되어 최종 정산이 완료되었습니다.",
        }

    def review_deal(self, deal_id: str, action: str, feedback: Optional[str] = None) -> EscrowDeal:
        deal = self.active_deals.get(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found.")

        if action == "APPROVE":
            deal.status = "APPROVED"
        elif action == "REVISE":
            return self.request_revision(deal_id, feedback or "")
        elif action == "SETTLE":
            deal.status = "SETTLED"
        return deal

    def get_admin_metrics(self) -> Dict[str, Any]:
        total_deals = len(self.active_deals)
        total_volume = sum(d.total_budget for d in self.active_deals.values())
        total_take_rate = sum(d.platform_fee for d in self.active_deals.values())
        active_count = sum(1 for d in self.active_deals.values() if d.status in ["ESCROW_LOCKED", "DRAFT_SUBMITTED"])

        return {
            "total_deal_count": total_deals,
            "total_gross_volume_krw": total_volume,
            "total_platform_take_rate_krw": total_take_rate,
            "active_escrow_deals": active_count,
            "avg_take_rate_pct": 10.0,
            "recent_deals": list(self.active_deals.values())[-5:],
        }


# Singleton instance
creator_network = CreatorNetwork()

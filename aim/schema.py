"""AIM (AI Platform Initiative) - Data Schemas
Defines Pydantic models for raw store data, unified business profile (Single Source of Truth),
and channel-specific marketing payloads.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# --- Data Governance: Evidence & Provenance (docs/12 Gate 0) ---

class EvidenceTier(str, Enum):
    """근거 등급: 수집 데이터가 실측/파생/시연 중 어디에 속하는지 규정한다.

    A_MEASURED     : 실제 API 또는 사용자 제공 파일에서 실측. 금전적 약속 전면 허용.
    B_DERIVED      : 실측값의 파생 통계. 카피 표현 근거 사용, 금액 약속 금지.
    C_ILLUSTRATIVE : 데모/샘플 고정값. 대시보드·의사결정에 절대 사용 금지.
    """
    A_MEASURED = "A_MEASURED"
    B_DERIVED = "B_DERIVED"
    C_ILLUSTRATIVE = "C_ILLUSTRATIVE"


class CollectionStatus(str, Enum):
    """수집 결과 상태. 실패를 숨기지 않기 위한 명시적 상태값."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED_NO_AUTH = "SKIPPED_NO_AUTH"
    SKIPPED_UNSUPPORTED = "SKIPPED_UNSUPPORTED"


class CollectionProvenance(BaseModel):
    """모든 수집기가 남겨야 하는 감사 장부 (Data Governance Officer 요구사항).

    이 장부를 남기지 않은 수집기는 운영 경로에 올릴 수 없다.
    """
    source_kind: str = Field(description="수집 소스 식별자 (예: 'KMA_WEATHER', 'POS_CSV', 'NAVER_PLACE')")
    request_target: str = Field(description="요청 URL 또는 파일명")
    fetched_at: str = Field(description="수집 완료 시각 (YYYY-MM-DD HH:MM:SS)")
    status: CollectionStatus
    failure_reason: Optional[str] = None
    record_count: int = 0
    pii_mask_applied: bool = False
    evidence_tier: EvidenceTier = EvidenceTier.C_ILLUSTRATIVE


class EnvironmentSignal(BaseModel):
    """외부 환경 컨텍스트 센서 (docs/12 4.4).

    기상청 API는 인증키가 필요하므로, 키 없이도 정확하게 계산 가능한
    천문·달력 신호를 먼저 확정하고 기상 실측은 키 확보 후 합류시킨다.
    """
    captured_at: str = Field(description="수집 시각 (YYYY-MM-DD HH:MM:SS)")
    observed_date: str = Field(description="관측 대상 날짜 (YYYY-MM-DD)")

    # -- 천문 계산 기반 (키 불필요, A_MEASURED) --
    solar_term: Optional[str] = Field(default=None, description="24절기 중 현재 해당 명칭")
    days_to_next_term: Optional[int] = Field(default=None, description="다음 절기까지 남은 일수")
    day_of_week: int = Field(default=0, description="0=월요일 ... 6=일요일")
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    is_bridged_day_off: bool = Field(default=False, description="공휴일과 겹친 대체공휴일")
    sunrise: Optional[str] = Field(default=None, description="일출 (HH:MM, KST)")
    sunset: Optional[str] = Field(default=None, description="일몰 (HH:MM, KST)")
    solar_noon: Optional[str] = Field(default=None, description="정오 (HH:MM, KST)")
    day_length: str = Field(default="", description="주간 길이 (예: '11시간 42분')")

    # -- 기상 실측 (수집기 미연결 시 None) --
    precip_prob: Optional[float] = Field(default=None, description="강수확률 0~1")
    precip_mm: Optional[float] = Field(default=None, description="시간당 강수량(mm)")
    temp_c: Optional[float] = Field(default=None, description="기온(℃)")
    weather_code: Optional[str] = Field(
        default=None, description="기상 현상 코드 원값 (체계는 weather_code_system이 지정)"
    )
    weather_code_system: Optional[str] = Field(
        default=None,
        description=(
            "'KMA_SKY' (기상청 단기예보, 0~9) 또는 'WMO' (Open-Meteo, 0~99). "
            "두 체계는 같은 숫자를 다른 뜻으로 쓰므로 반드시 명시해야 하며 "
            "추측하지 않는다 (docs/17 §2)."
        ),
    )

    evidence_tier: EvidenceTier = Field(
        default=EvidenceTier.A_MEASURED,
        description="천문·달력 계산은 A_MEASURED, 기상 필드가 None이면 해당 축은 미수집",
    )
    collection: Optional[CollectionProvenance] = None

    @property
    def has_weather(self) -> bool:
        return self.temp_c is not None or self.precip_prob is not None


# --- Offline POS Ledger Fact (docs/12 P0-2) ---

class SalesLedgerFact(BaseModel):
    """정산 파일 1건에서 직접 계산한 영업일 실측 사실 (docs/12 4.1).

    이 모델이 존재하는 이유는 단 하나입니다. 예전에 유휴율·객단가는
    테스트베드 하드코딩값(C_ILLUSTRATIVE)이었고, 그 값으로 매출을 약속했습니다.
    사장님이 준 정산 파일에서 직접 계산한 값만 A_MEASURED로 승격시킵니다.

    필드명에 대한 의도적 편차: docs/12 4.1은 필드를 `slot_occupancy`로
    적었지만 괄호 주석은 "(0~1 유휴율)"이었습니다.occupancy는 통상 만석률을
    뜻하므로, 유휴율 값에 그 이름을 쓰면 나중에 반대로 읽힙니다.
    따라서 `slot_idle_rate`(유휴율)로 명명하고 평균값을 `idle_capacity_rate`
    프로퍼티로 노출합니다. 의미는 문서 주석(유휴율)이 우선입니다.
    """
    source: str = Field(description="'POS_FILE' | 'PAYMENT_GATEWAY' | 'RESERVATION_LOG'")
    captured_at: str = Field(description="수집 시각 (YYYY-MM-DD HH:MM:SS)")
    business_date: str = Field(description="영업일 (YYYY-MM-DD)")
    transaction_count: int = 0
    gross_revenue_krw: int = 0
    avg_ticket_krw: int = 0
    slot_idle_rate: Dict[str, float] = Field(
        default_factory=dict,
        description="시간대별 유휴율 0~1. 0=만석, 1=전좌석 유휴",
    )
    low_stock_items: List[str] = Field(default_factory=list)
    evidence_tier: EvidenceTier = Field(
        default=EvidenceTier.A_MEASURED,
        description="정산 파일에서 직접 계산한 값만 A_MEASURED로 승격된다",
    )
    collection: Optional[CollectionProvenance] = None

    @property
    def idle_capacity_rate(self) -> float:
        """시간대 단순평균 유휴율. BusinessState.idle_capacity_rate 대체값."""
        if not self.slot_idle_rate:
            return 0.0
        return round(sum(self.slot_idle_rate.values()) / len(self.slot_idle_rate), 4)


# --- Raw Ingestion Models ---

class StoreInfo(BaseModel):
    store_id: str
    name: str
    category: str
    address: str
    business_hours: str
    usp_highlights: List[str] = Field(default_factory=list)


class TopSellingItem(BaseModel):
    item_name: str
    sales_count: int
    unit_price: int


class PosSummary(BaseModel):
    analysis_period: str
    top_selling_items: List[TopSellingItem] = Field(default_factory=list)
    peak_hours: str
    low_stock_risk_item: Optional[str] = None
    evidence_tier: EvidenceTier = Field(
        default=EvidenceTier.C_ILLUSTRATIVE,
        description="POS 연동 전까지 항상 시연값. 금전적 약속 근거로 사용 금지.",
    )


class RawReview(BaseModel):
    review_id: str
    source: str
    author: str
    rating: float
    text: str


class Promotion(BaseModel):
    promo_id: str
    title: str
    benefit: str
    valid_until: str


class RawStoreData(BaseModel):
    store_info: StoreInfo
    pos_summary: PosSummary
    raw_reviews: List[RawReview] = Field(default_factory=list)
    current_promotions: List[Promotion] = Field(default_factory=list)
    collection: Optional[CollectionProvenance] = Field(
        default=None, description="이 데이터를 만든 수집기의 감사 장부"
    )


# --- Normalized Single Source of Truth Models ---

class NormalizedProduct(BaseModel):
    name: str
    sales_volume_desc: str
    unit_price: int
    highlights: List[str] = Field(default_factory=list)


class UnifiedBusinessProfile(BaseModel):
    """The Single Source of Truth DB representation for AI Multi-Agent orchestration."""
    store_id: str
    store_name: str
    category: str
    address: str
    business_hours: str
    core_usps: List[str]
    hero_products: List[NormalizedProduct]
    positive_signals: List[str]
    pain_points: List[str]
    context_tags: List[str]
    active_promotion: Optional[Dict[str, str]] = None


# --- Compliance & Safety Models ---

class ComplianceViolation(BaseModel):
    original_term: str
    rule_category: str
    severity: str  # 'HIGH' (Blocker), 'MEDIUM' (Warning)
    recommended_term: str
    reason: str


class ComplianceReport(BaseModel):
    is_compliant: bool
    violations: List[ComplianceViolation] = Field(default_factory=list)
    original_text: str
    sanitized_text: str


# --- Generated Channel Payloads ---

class VisualAssetSpec(BaseModel):
    ratio: str
    format_type: str
    layout_description: str
    recommended_copy_overlay: str


class ChannelContent(BaseModel):
    channel: str  # 'naver_blog', 'instagram', 'kakaotalk'
    tone: str = "MZ_TREND"  # 'MZ_TREND', 'WORKER_HEALING', 'LOCAL_FAMILY'
    headline: str
    body: str
    call_to_action: str
    hashtags: List[str] = Field(default_factory=list)
    visual_spec: VisualAssetSpec
    compliance_report: Optional[ComplianceReport] = None


class MarketingPackage(BaseModel):
    store_id: str
    generated_at: str
    tone: str = "MZ_TREND"
    channels: Dict[str, ChannelContent]
    all_compliant: bool
    geo_schema_jsonld: Optional[Dict[str, Any]] = None


# --- Multi-Industry 6D Contextual Testbed Models ---

class ContextProvenance(BaseModel):
    """6D 벡터를 구성할 때 실제로 사용한 데이터 소스 (docs/19).

    왜 이 축이 필요한가: 상황 문자열만으로는 "이 카피가 실측 기상을 썼는가"를
    증명할 수 없다. 문자열로 추측하면 문서 16 §7.1의 부분일치 오탐과 같은
    함정에 빠진다. 출처는 **텍스트가 아니라 데이터로** 기록해야 한다.

    특히 Open-Meteo 데이터는 CC BY 4.0이라 출처 표기가 법적 의무다.
    '방금 기상청을 조회했다'는 사실은 조회 로그에만 있고 산출물에 남지 않으면
    표기 의무를 판정할 근거가 사라진다.
    """
    sources: List[str] = Field(
        default_factory=lambda: ["ASTRONOMY_CALENDAR"],
        description="6D 벡터에 실제로 기여한 수집 소스 식별자",
    )
    weather_collected: bool = Field(
        default=False, description="실측 기상 필드가 채워졌는지 여부"
    )
    required_attribution: Optional[str] = Field(
        default=None,
        description="이 컨텍스트로 만든 산출물에 반드시 표기해야 할 출처 문구 (라이선스 의무)",
    )
    collection: Optional[CollectionProvenance] = None


class Context6D(BaseModel):
    era: str = Field(description="시대적 메가트렌드 (예: AI 자동화, 헬시플레저)")
    situation: str = Field(description="실시간 상황 (예: 가을비 예보, 노쇼 1건, 유휴 라인)")
    season: str = Field(description="시즌/절기 (예: 환절기, Q4 연말 결산, 조달 시즌)")
    generation: str = Field(description="세대/타깃 (예: 2030 MZ, 3040 전문직, 4050 구매팀)")
    region: str = Field(description="지역/입지 (예: 성수동 핫플, 강남 역세권, 창원 산단, 글로벌)")
    milestone: str = Field(description="고객 생애주기/계기 (예: 100일 기념, 결혼 D-60, 온보딩 48시간)")
    provenance: ContextProvenance = Field(
        default_factory=ContextProvenance,
        description="이 벡터를 만든 데이터 출처. 문자열이 아니라 데이터로 기록한다.",
    )


class SimulatedActionBundle(BaseModel):
    action_title: str
    channel_1_blog: str
    channel_2_insta: str
    channel_3_direct: str
    compliance_check: str
    expected_roi: str


class IndustryTestbedProfile(BaseModel):
    id: str
    industry_type: str
    name: str
    location: str
    target_audience: str
    core_usps: List[str]
    current_pain_or_event: str
    context_6d: Context6D
    simulated_actions: SimulatedActionBundle


# --- Platform Architecture Core Schemas ---

class BusinessState(BaseModel):
    """Canonical representation of an arbitrary business entity's operational state."""
    domain: str = Field(description="Domain category: 'fnb', 'medical', 'beauty', 'b2b_saas', 'manufacturing'")
    entity_name: str
    location: str
    target_audience: str
    core_usps: List[str]
    idle_capacity_rate: float = Field(default=0.0, description="0.0 to 1.0 (empty tables, doctor slot, CNC line)")
    trigger_event: str = Field(description="Real-time operational event or pain point")
    unit_price: int = Field(default=0, description="Average unit transaction price in KRW")
    pending_leads_count: int = Field(default=0, description="No-shows, recall due, churn risk, or RFQ count")
    context_tags: List[str] = Field(default_factory=list)


class StrategyObjective(BaseModel):
    """Output of StrategyEngine: Strategic goal and tactical campaign plan."""
    objective_type: str = Field(
        description="'CAPACITY_RESCUE', 'RETENTION_RECALL', 'VIRAL_EXPANSION', 'OPPORTUNITY_CAPTURE'"
    )
    campaign_title: str
    target_persona: str
    core_narrative: str
    incentive_offer: Optional[str] = None
    urgency_level: str = Field(default="MEDIUM", description="'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'")
    recommended_channels: List[str] = Field(default_factory=list)
    projected_additional_units: int = 0
    projected_revenue: int = 0
    estimated_cost: int = 0
    expected_roi_ratio: float = 0.0


class ChannelPayload(BaseModel):
    """Generated marketing copy and metadata for a specific distribution channel."""
    channel_key: str  # 'blog', 'social', 'direct'
    channel_display_name: str
    headline: str
    body: str
    call_to_action: str
    hashtags: List[str] = Field(default_factory=list)
    compliance_report: ComplianceReport
    attribution: Optional[str] = Field(
        default=None,
        description="라이선스가 요구하는 출처 표기. 기상 데이터가 사용되었으면 필수.",
    )


class PlatformMarketingPlan(BaseModel):
    """End-to-End Orchestrated Plan generated by the AIM Platform Kernel."""
    plan_id: str
    entity_name: str
    domain: str
    generated_at: str
    context_vector: Context6D
    strategy: StrategyObjective
    channels: Dict[str, ChannelPayload]
    all_compliant: bool
    summary_financials: Dict[str, Any]
    attribution: Optional[str] = Field(
        default=None,
        description="계획 전체에 적용되는 출처 표기 (라이선스 의무)",
    )


CampaignPlan = PlatformMarketingPlan

# --- Multi-Tenant & Platform Master Administration Schemas ---

class TenantAccount(BaseModel):
    """Paid Subscriber Business Account (유료 가입자 테넌트 계정)."""
    tenant_id: str
    business_name: str
    owner_name: str
    domain: str
    subscription_tier: str = Field(default="PRO", description="'FREE', 'PRO' (49k), 'ENTERPRISE' (199k)")
    monthly_fee_krw: int = Field(default=49000)
    status: str = Field(default="ACTIVE", description="'ACTIVE', 'PAUSED', 'TRIAL'")
    joined_at: str
    business_state: BusinessState
    cumulative_revenue_generated_krw: int = Field(default=0)
    total_campaigns_executed: int = Field(default=0)


class ComplianceAuditLogEntry(BaseModel):
    """Platform-wide compliance interception record for Super-Admin inspection."""
    log_id: str
    tenant_id: str
    business_name: str
    domain: str
    timestamp: str
    intercepted_term: str
    rule_category: str
    severity: str
    sanitized_to: str


class PlatformMasterKPI(BaseModel):
    """Executive KPI Metrics for the Platform Super-Admin War Room."""
    total_active_tenants: int
    total_mrr_krw: int
    total_platform_value_krw: int
    average_roi_multiplier: float
    total_compliance_blocks: int
    system_uptime_percent: float = 99.98
    agent_worker_status: Dict[str, str] = Field(default_factory=dict)

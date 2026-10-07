"""AIM (AI Platform Initiative) - Tenant Management Service
Manages paid subscriber business accounts, subscriptions, and tenant-specific ROI analytics.
"""

from typing import Dict, List, Optional
from aim.schema import TenantAccount, BusinessState


class TenantManager:
    """Multi-tenant subscriber registry and workspace controller."""

    _tenants: Dict[str, TenantAccount] = {}

    @classmethod
    def _initialize_defaults(cls) -> None:
        if cls._tenants:
            return

        cls._tenants = {
            "TENANT_001": TenantAccount(
                tenant_id="TENANT_001",
                business_name="성수 아뜰리에 베이커리 & 카페",
                owner_name="김성수 대표",
                domain="fnb",
                subscription_tier="PRO",
                monthly_fee_krw=49000,
                status="ACTIVE",
                joined_at="2026-08-15",
                business_state=BusinessState(
                    domain="fnb",
                    entity_name="성수 아뜰리에 베이커리 & 카페",
                    location="서울 성동구 성수동 핫플레이스 상권",
                    target_audience="2030 MZ세대, 빵지순례객, 반려견 동반족",
                    core_usps=[
                        "프랑스 AOP 버터 100% 천연발효 사워도우",
                        "당일 생산 당일 소진 원칙",
                        "반려동물 동반 가능 야외 테라스",
                    ],
                    idle_capacity_rate=0.35,
                    trigger_event="오늘 오후 15시 비 예보 + 2시 이후 사워도우 조기 품절",
                    unit_price=24000,
                    pending_leads_count=12,
                ),
                cumulative_revenue_generated_krw=4320000,
                total_campaigns_executed=12,
            ),
            "TENANT_002": TenantAccount(
                tenant_id="TENANT_002",
                business_name="강남 리엔 피부과의원",
                owner_name="이지현 대표원장",
                domain="medical",
                subscription_tier="ENTERPRISE",
                monthly_fee_krw=199000,
                status="ACTIVE",
                joined_at="2026-07-01",
                business_state=BusinessState(
                    domain="medical",
                    entity_name="강남 리엔 피부과의원",
                    location="서울 강남구 신논현 오피스/뷰티 상권",
                    target_audience="2545 직장인 여성, 예비 신부, 리프팅 주기 도래 고객",
                    core_usps=[
                        "피부과 전문의 1:1 맞춤 진단",
                        "정품 정량 100% 현장 개봉 원칙",
                        "프라이빗 1인 관리실 완비",
                    ],
                    idle_capacity_rate=0.10,
                    trigger_event="오늘 16:30 의사 2원장 시술 예약 노쇼(취소) 1건 발생 + 보톡스 시술 90일 경과 환자 48명",
                    unit_price=250000,
                    pending_leads_count=48,
                ),
                cumulative_revenue_generated_krw=26400000,
                total_campaigns_executed=18,
            ),
            "TENANT_003": TenantAccount(
                tenant_id="TENANT_003",
                business_name="청담 아우라 헤어살롱",
                owner_name="박준우 원장",
                domain="beauty",
                subscription_tier="PRO",
                monthly_fee_krw=49000,
                status="ACTIVE",
                joined_at="2026-09-01",
                business_state=BusinessState(
                    domain="beauty",
                    entity_name="청담 아우라 헤어살롱",
                    location="서울 강남구 청담동 럭셔리 뷰티 상권",
                    target_audience="2040 트렌드세터, 컷트 4주/염색 8주 도래 단골",
                    core_usps=[
                        "퍼스널 컬러 & 얼굴형 분석 1:1 맞춤 컨설팅",
                        "프리미엄 비건 헤어 케어 라인 사용",
                        "단독 샴푸 스파 룸 구비",
                    ],
                    idle_capacity_rate=0.60,
                    trigger_event="내일 목요일 13:00~16:00 유휴 의자(빈 좌석) 6석 발생",
                    unit_price=130000,
                    pending_leads_count=6,
                ),
                cumulative_revenue_generated_krw=7800000,
                total_campaigns_executed=14,
            ),
            "TENANT_004": TenantAccount(
                tenant_id="TENANT_004",
                business_name="플로우독 (FlowDoc) - AI 협업 툴",
                owner_name="최진혁 파운더",
                domain="b2b_saas",
                subscription_tier="PRO",
                monthly_fee_krw=49000,
                status="ACTIVE",
                joined_at="2026-06-15",
                business_state=BusinessState(
                    domain="b2b_saas",
                    entity_name="플로우독 (FlowDoc) - AI 협업 툴",
                    location="온라인 / 판교 테크노밸리 & 글로벌 원격",
                    target_audience="IT 스타트업 팀장, 프로젝트 매니저(PM), 개발팀",
                    core_usps=[
                        "깃허브 이슈-기획서 실시간 양방향 동기화",
                        "AI 자동 회의록 및 액션 아이템 추출",
                        "슬랙/지라 원클릭 연동",
                    ],
                    idle_capacity_rate=0.15,
                    trigger_event="v2.4 신기능(AI 스프린트 회고) 배포 완료 + 가입 48시간 내 미사용 이탈 위험군 120명",
                    unit_price=200000,
                    pending_leads_count=120,
                ),
                cumulative_revenue_generated_krw=16800000,
                total_campaigns_executed=9,
            ),
            "TENANT_005": TenantAccount(
                tenant_id="TENANT_005",
                business_name="대진정밀공업 (CNC·사출 가공)",
                owner_name="정대진 총괄전무",
                domain="manufacturing",
                subscription_tier="ENTERPRISE",
                monthly_fee_krw=199000,
                status="ACTIVE",
                joined_at="2026-05-10",
                business_state=BusinessState(
                    domain="manufacturing",
                    entity_name="대진정밀공업 (CNC·사출 가공)",
                    location="경남 창원 국가산업단지 & 글로벌 수출",
                    target_audience="국내외 자동차 부품사, 방산·로봇 기구 설계 구매팀",
                    core_usps=[
                        "5축 머시닝 센터 공차 ±0.005mm 정밀 가공",
                        "IATF 16949 & ISO 9001 글로벌 품질 인증",
                        "알루미늄/티타늄 난삭재 전문 가공",
                    ],
                    idle_capacity_rate=0.35,
                    trigger_event="2주 뒤 3호 사출 라인 유휴 캐파 35% 발생 + LME 알루미늄 국제 시세 7% 일시 하락",
                    unit_price=22500000,
                    pending_leads_count=2,
                ),
                cumulative_revenue_generated_krw=90000000,
                total_campaigns_executed=4,
            ),
        }

    @classmethod
    def list_tenants(cls) -> List[TenantAccount]:
        cls._initialize_defaults()
        return list(cls._tenants.values())

    @classmethod
    def get_tenant(cls, tenant_id: str) -> Optional[TenantAccount]:
        cls._initialize_defaults()
        return cls._tenants.get(tenant_id)

    @classmethod
    def update_status(cls, tenant_id: str, new_status: str) -> Optional[TenantAccount]:
        cls._initialize_defaults()
        tenant = cls._tenants.get(tenant_id)
        if tenant:
            tenant.status = new_status
        return tenant

    @classmethod
    def update_subscription_tier(cls, tenant_id: str, new_tier: str) -> Optional[TenantAccount]:
        cls._initialize_defaults()
        tenant = cls._tenants.get(tenant_id)
        if tenant:
            tenant.subscription_tier = new_tier
            tenant.monthly_fee_krw = 199000 if new_tier == "ENTERPRISE" else (49000 if new_tier == "PRO" else 0)
        return tenant

    @classmethod
    def record_campaign_execution(cls, tenant_id: str, generated_revenue: int) -> None:
        cls._initialize_defaults()
        tenant = cls._tenants.get(tenant_id)
        if tenant:
            tenant.total_campaigns_executed += 1
            tenant.cumulative_revenue_generated_krw += generated_revenue

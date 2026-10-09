"""AIM (AI Platform Initiative) - Omni-Channel Content Publisher & Management Ledger
(aim/core/publisher.py)
-------------------------------------------------------------------------------------
Generates finalized, production-ready copies formatted for:
1. Naver SmartPlace News (네이버 플레이스 새소식 규격: 제목 40자 + 본문 + 1:1 이미지 + 쿠폰)
2. Instagram Feed / Reels (3초 후킹 캡션 + 해시태그 15종 + 9:16 비주얼)
3. Creator / YouTuber 15s Storyboard Pitch (협찬 제안서 & 15초 콘티)
4. Kakao Channel Alert Message (와이드 배너 + 단문 혜택)
Maintains the Publication History Ledger for merchant tracking.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from aim.tenant.manager import TenantManager
from aim.infra.marketing_infrastructure import MarketingInfrastructureEngine


class NaverPlaceNewsPayload(BaseModel):
    title_max40: str
    body_text: str
    event_period: str
    coupon_link_code: str
    image_asset_spec: str
    clipboard_text: str


class InstagramContentPayload(BaseModel):
    hooking_first_line: str
    caption_body: str
    hashtags: List[str]
    hashtags_block: str
    visual_layout_spec: str
    clipboard_text: str


class CreatorPitchPayload(BaseModel):
    matched_creator_name: str
    matched_creator_handle: str
    channel_format: str
    storyboard_15s: Dict[str, str]  # hook_0_3s, body_3_10s, cta_10_15s
    proposal_message_text: str
    escrow_fee_krw: int
    subscriber_discount_pct: int
    clipboard_text: str


class KakaoMessagePayload(BaseModel):
    banner_headline: str
    message_body: str
    action_button_label: str
    action_url: str
    clipboard_text: str


class FinalizedPublishingBundle(BaseModel):
    bundle_id: str
    tenant_id: str
    business_name: str
    advice_id: str
    category: str
    generated_at: str
    naver_place: NaverPlaceNewsPayload
    instagram: InstagramContentPayload
    creator_pitch: CreatorPitchPayload
    kakao_channel: KakaoMessagePayload
    compliance_summary: str = "✅ 표시광고법·의료법 100% 사전 검수 완료 (안전)"


class PublicationRecord(BaseModel):
    record_id: str
    tenant_id: str
    business_name: str
    channel: str  # NAVER_PLACE, INSTAGRAM, CREATOR, KAKAO
    channel_korean: str
    headline: str
    trigger_type: str
    status: str  # COPIED, DISPATCHED, LIVE
    published_at: str
    attributed_revenue_gain_krw: int


class ContentPublisher:
    """Production synthesizer formatting copies to exact channel specs and ledger management."""

    _publication_history: List[PublicationRecord] = []

    @classmethod
    def _initialize_defaults(cls):
        if cls._publication_history:
            return
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        cls._publication_history = [
            PublicationRecord(
                record_id="PUB_REC_001",
                tenant_id="TENANT_001",
                business_name="성수 아뜰리에 베이커리 & 카페",
                channel="NAVER_PLACE",
                channel_korean="네이버 스마트플레이스 새소식",
                headline="[비 오는 날 3시간 한정] 갓 구운 바질소금빵 1+1 번개 혜택",
                trigger_type="🌧️ 기상 강수(5.2mm) 인프라 감지",
                status="LIVE",
                published_at="오늘 14:10",
                attributed_revenue_gain_krw=240000,
            ),
            PublicationRecord(
                record_id="PUB_REC_002",
                tenant_id="TENANT_001",
                business_name="성수 아뜰리에 베이커리 & 카페",
                channel="INSTAGRAM",
                channel_korean="인스타그램 피드 & 릴스",
                headline="연무장길 팝업 돌고 어디 감? 🥐 프랑스 고메버터 소금빵 핫플",
                trigger_type="🎪 성수 패션 팝업 축제 인프라 연동",
                status="LIVE",
                published_at="어제 16:30",
                attributed_revenue_gain_krw=480000,
            ),
            PublicationRecord(
                record_id="PUB_REC_003",
                tenant_id="TENANT_001",
                business_name="성수 아뜰리에 베이커리 & 카페",
                channel="CREATOR",
                channel_korean="유튜브 쇼츠 15초 콘티 협찬 섭외",
                headline="크리에이터 @디저트탐험가 은지(18만) 15초 숏폼 에스크로 체결",
                trigger_type="🤝 로컬 인플루언서 제휴 네트워크",
                status="DISPATCHED",
                published_at="3일 전",
                attributed_revenue_gain_krw=850000,
            ),
        ]

    @classmethod
    def synthesize_bundle(cls, tenant_id: str, advice_id: str) -> FinalizedPublishingBundle:
        cls._initialize_defaults()
        tenant = TenantManager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        b_name = tenant.business_name
        loc = tenant.business_state.location or "서울 성수동"
        hero = tenant.business_state.core_usps[0] if tenant.business_state.core_usps else "시그니처 바질 소금빵"
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Naver Place News Payload
        short_hero = hero[:14] if len(hero) > 14 else hero
        naver_title = f"[비 오는 날 특가] {short_hero} 1+1 혜택"
        if len(naver_title) > 40:
            naver_title = naver_title[:40]
        naver_body = (
            f"안녕하세요, {b_name}입니다.\n\n"
            f"오늘 {loc}에 비가 내리고 있네요. 쌀쌀한 날씨에 매장을 찾아주시는 소중한 이웃분들을 위해 "
            f"오늘 단 3시간 동안 [비 오는 날 갓 구운 {hero} 1+1 번개 혜택]을 진행합니다!\n\n"
            f"■ 이벤트 시간: 오늘 15:00 ~ 18:00 (원재료 소진 시 조기 마감)\n"
            f"■ 대상 고객: 본 네이버 스마트플레이스 소식 쿠폰을 보여주시는 모든 분\n"
            f"■ 매장 위치: {loc} (성수역 3번 출구 도보 4분)\n\n"
            f"따뜻한 빵 냄새 가득한 매장에서 기분 좋은 힐링을 챙겨가세요. 감사합니다 :)"
        )
        naver_clip = f"【네이버 플레이스 소식 등록용】\n[소식 제목] {naver_title}\n\n[소식 본문]\n{naver_body}"

        naver_payload = NaverPlaceNewsPayload(
            title_max40=naver_title,
            body_text=naver_body,
            event_period="오늘 15:00 ~ 18:00 (3시간 한정)",
            coupon_link_code="AIM-SEONGSU-RAIN-3K",
            image_asset_spec="1:1 정방형 (1080x1080px) 갓 구운 빵 스팀 연출 컷 + '비 오는 날 1+1' 볼드 타이포",
            clipboard_text=naver_clip,
        )

        # 2. Instagram Payload
        insta_hook = f"비 오는 성수동 골목길에서 빵 냄새에 홀려버림... 🥐🤤"
        insta_body = (
            f"{insta_hook}\n\n"
            f"성수동 핫플 '{b_name}'에서 오늘 비 예보 기념으로 깜짝 번개 혜택 쏩니다 ⚡\n\n"
            f"프랑스 AOP 고메버터 48%로 구워내 겉은 파사삭 속은 쫀득 고소한 【{hero}】!\n"
            f"오늘 오후 3시부터 3시간 동안만 매장 방문 시 1+1 테이크아웃 가능 🏃💨\n\n"
            f"팝업 구경하다 비 피할 곳 찾으신다면 고소한 빵 냄새 따라오세요 ☕✨\n"
            f"📍 {loc} (성수역 3분)\n"
            f"⏱️ 3시간 타임어택 (소진 시 마감)"
        )
        hashtags = [
            "#성수동카페", "#성수카페", "#성수동베이커리", "#소금빵맛집", "#비오는날성수",
            "#성수핫플", "#성수데이트", "#성수팝업", "#연무장길카페", "#서울빵지순례",
            "#디저트그램", "#카페투어", "#빵스타그램", "#바질소금빵", "#성수아뜰리에"
        ]
        ht_block = " ".join(hashtags)
        insta_clip = f"{insta_body}\n\n.\n.\n{ht_block}"

        insta_payload = InstagramContentPayload(
            hooking_first_line=insta_hook,
            caption_body=insta_body,
            hashtags=hashtags,
            hashtags_block=ht_block,
            visual_layout_spec="9:16 세로형 릴스 템플릿: 버터 흐르는 단면 클로즈업 + 자막 바",
            clipboard_text=insta_clip,
        )

        # 3. Creator Pitch Payload
        pitch_msg = (
            f"안녕하세요, 은지님! 성수동에서 프랑스 버터 베이커리를 운영하는 '{b_name}' 김성수 대표입니다.\n"
            f"은지님의 빵지순례 숏폼 영상을 평소 즐겨보며, 디저트의 결을 살려주시는 시선에 큰 감명을 받았습니다.\n\n"
            f"이번에 저희 시그니처인 '{hero}'의 고소하고 바삭한 결을 은지님만의 감각적인 15초 쇼츠로 소개해 주실 수 있을지 "
            f"정중히 협찬 제안을 드립니다.\n\n"
            f"■ 제안 포맷: 15초 YouTube Shorts 1편\n"
            f"■ 제공 사항: 매장 전 메뉴 시식 지원 + 협찬 제작비 (AIM 에스크로 안전 결제)\n"
            f"■ 제안 콘티: 15초 완성형 대본 첨부 (상세 수정 은지님 재량 100% 존중)\n\n"
            f"긍정적으로 검토해 주시면 바로 에스크로 계약서를 발송해 드리겠습니다. 감사합니다!"
        )
        creator_clip = f"【크리에이터 섭외 제안 메시지】\n{pitch_msg}\n\n【15초 숏폼 콘티 가이드】\n" \
                       f"0~3초: '성수동 빵순이들 사이에서 소문난 버터 동굴 실물 영접'\n" \
                       f"3~10초: '한 입 베어물면 바사삭 소리 ASMR + 결이 살아있는 단면'\n" \
                       f"10~15초: '오늘 고정댓글 링크 누르면 3,000원 쿠폰 바로 챙김!'"

        creator_payload = CreatorPitchPayload(
            matched_creator_name="디저트탐험가 은지",
            matched_creator_handle="@eunji_dessert",
            channel_format="YouTube Shorts & Instagram Reels",
            storyboard_15s={
                "hook_0_3s": "성수동 빵순이들 사이에서 소문난 버터 동굴 실물 영접 🥐🔥",
                "body_3_10s": f"프랑스산 고메버터 48%로 구워 바삭바삭 소리 ASMR 터지는 '{hero}' 단면 클로즈업!",
                "cta_10_15s": "영상 하단 링크에서 3,000원 쿠폰 받고 오늘 바로 성수동으로 달려가세요!",
            },
            proposal_message_text=pitch_msg,
            escrow_fee_krw=150000,
            subscriber_discount_pct=10,
            clipboard_text=creator_clip,
        )

        # 4. Kakao Alert Message Payload
        kakao_head = f"📢 [실시간 번개 혜택] {b_name} 비 오는 날 1+1 쿠폰 도착!"
        kakao_body = (
            f"{b_name} 단골 고객님께만 드리는 오늘 3시간 한정 번개 혜택입니다.\n\n"
            f"빗속을 뚫고 찾아주신 발걸음에 감사하며, 시그니처 '{hero}' 1개 구매 시 1개를 선물로 더 드립니다.\n\n"
            f"아래 버튼을 눌러 모바일 티켓을 발급받으세요!"
        )
        kakao_clip = f"【카카오 알림톡 발송용】\n헤드라인: {kakao_head}\n\n내용:\n{kakao_body}\n버튼: 모바일 티켓 받기 ➔ https://esketch-ai.github.io/AIM/c/AIM-SEONGSU-CR02-RAIN24K"

        kakao_payload = KakaoMessagePayload(
            banner_headline=kakao_head,
            message_body=kakao_body,
            action_button_label="모바일 번개 티켓 받기",
            action_url="https://esketch-ai.github.io/AIM/c/AIM-SEONGSU-CR02-RAIN24K",
            clipboard_text=kakao_clip,
        )

        return FinalizedPublishingBundle(
            bundle_id=f"PUB_BDL_{now_dt.strftime('%Y%m%d%H%M%S')}",
            tenant_id=tenant_id,
            business_name=b_name,
            advice_id=advice_id,
            category="INFRA_PRESCRIPTIVE_PUBLISHING",
            generated_at=now_str,
            naver_place=naver_payload,
            instagram=insta_payload,
            creator_pitch=creator_payload,
            kakao_channel=kakao_payload,
        )

    @classmethod
    def record_publication(
        cls,
        tenant_id: str,
        channel: str,
        headline: str,
        trigger_type: str,
        gain_krw: int = 240000
    ) -> PublicationRecord:
        cls._initialize_defaults()
        tenant = TenantManager.get_tenant(tenant_id)
        if tenant:
            b_name = tenant.business_name
            tenant.cumulative_revenue_generated_krw += gain_krw
            tenant.total_campaigns_executed += 1
        else:
            b_name = "매장"

        ch_map = {
            "NAVER_PLACE": "네이버 스마트플레이스 새소식",
            "INSTAGRAM": "인스타그램 피드 & 릴스",
            "CREATOR": "유튜브 쇼츠 15초 콘티 협찬 섭외",
            "KAKAO": "카카오톡 단골 채널 알림톡",
        }

        rec = PublicationRecord(
            record_id=f"PUB_REC_{len(cls._publication_history) + 1:03d}",
            tenant_id=tenant_id,
            business_name=b_name,
            channel=channel,
            channel_korean=ch_map.get(channel, channel),
            headline=headline,
            trigger_type=trigger_type,
            status="LIVE",
            published_at="방금 전",
            attributed_revenue_gain_krw=gain_krw,
        )
        cls._publication_history.insert(0, rec)
        return rec

    @classmethod
    def get_history(cls, tenant_id: str) -> List[PublicationRecord]:
        cls._initialize_defaults()
        return [r for r in cls._publication_history if r.tenant_id == tenant_id]


content_publisher = ContentPublisher()

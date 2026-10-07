"""AIM (AI Platform Initiative) - Multi-Channel & Multi-Tone Content Generator
Supports targeted audience tones:
1. MZ_TREND: 2030 Hipster, Dopamine-hooking, Short-form, Witty Slangs & Emojis
2. WORKER_HEALING: 3040 Busy Workers, Stress Relief, Practical Coffee/Brunch Tips
3. LOCAL_FAMILY: 4050+ Neighborhood Families, Clean/Healthy Ingredients, Trust & Warmth
"""

import re
from typing import Dict
from aim.schema import (
    UnifiedBusinessProfile,
    ChannelContent,
    VisualAssetSpec,
)
from aim.compliance import ComplianceGuard


def clean_markdown_spacing(text: str) -> str:
    """Ensures strict CommonMark spacing around bold tags, headings, and lists."""
    text = re.sub(r"^(#{1,6})([^\s#])", r"\1 \2", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*:\s*", r"**\1** : ", text)
    text = re.sub(r"^-([^\s])", r"- \1", text, flags=re.MULTILINE)
    return text.strip()


class MultiChannelGenerator:
    """Generates channel-specific copies adapted to target audience tones."""

    # =========================================================================
    # 1. NAVER BLOG GENERATOR (By Tone)
    # =========================================================================
    @classmethod
    def generate_naver_blog(cls, profile: UnifiedBusinessProfile, tone: str = "MZ_TREND") -> ChannelContent:
        hero = profile.hero_products[0] if profile.hero_products else None
        hero_name = hero.name if hero else "시그니처 메뉴"
        price_str = f"{hero.unit_price:,}원" if hero else ""
        store = profile.store_name

        usp1 = profile.core_usps[0] if profile.core_usps else "엄선된 프리미엄 원재료 사용"
        usp2 = profile.core_usps[1] if len(profile.core_usps) > 1 else "당일 생산 당일 판매 원칙"
        pain = profile.pain_points[0] if profile.pain_points else "인기 메뉴는 오후 조기 품절 주의!"
        hours = profile.business_hours or "10:00 - 21:00"

        if tone == "MZ_TREND":
            headline = f"성수동 빵순이의 찐 털이! 2시 전에 안 가면 품절각인 '{store}' 솔직 리뷰 🥐🔥"
            body = f"""# [성수 핫플] 나만 알고 싶었는데 이미 유명해진 '{store}' 솔직 후기

다들 혈중 버터 농도 부족할 때 어디 가시나요? 🤤  
성수동 골목길에서 고소한 빵 냄새에 홀려서 들어갔다가 그대로 인생 빵집 등극해버린 **'{store}'** 다녀왔습니다!

---

## 🔥 1. 왜 이렇게 난리인가 했더니? (USP 체크)

일단 화려하기만 한 인스타용 카페랑은 차원이 다름... 
- **{usp1}**
- **{usp2}**

한 입 베어 무는 순간 '바사삭' 소리 나면서 속은 쫀득 촉촉... 식감 폼 진짜 미쳤습니다;;

---

## 🥐 2. 무조건 담아야 할 원픽 : {hero_name} ({price_str})

오픈런 뛰어서 겟한 **{hero_name}**!  
원물 아낌없이 쏟아부어서 묵직한 거 실화냐구요... 치즈랑 조합이 그냥 반칙입니다.

> **내돈내산 찐 한줄평** :  
> "성수동에서 이 정도 퀄리티면 웨이팅 1시간도 인정함 ☕"

---

## ⚠️ 3. 헛걸음 방지 필수 꿀팁 (방문 전 필독)

- **오후 2시 품절각** : {pain}
- **댕댕이 동반 테라스** : 반려견이랑 브런치 때리기 딱 좋은 분위기 🐶🤍
- **영업 시간** : {hours}

{f"🎁 **개이득 프로모션** : {profile.active_promotion['title']} ({profile.active_promotion['benefit']})" if profile.active_promotion else ""}
"""
            cta = f"📍 성수동 갈 일 있으면 저장해두고 꼭 오픈런 뛰어보세요! 빵순이 지갑 탈탈 털림 주의 💸"

        elif tone == "WORKER_HEALING":
            headline = f"퇴근길 소확행 & 출근길 빵모닝! 성수 직장인 추천 '{store}' 이용 꿀팁 ☕"
            body = f"""# [직장인 힐링 스팟] 바쁜 일상 속 작은 위로, {store}

월요병과 야근에 지칠 때, 따뜻한 커피 한 잔과 갓 구운 빵 한 조각만큼 확실한 치유제가 있을까요?  
성수동 직장인들의 숨은 아지트, **'{store}'**를 소개합니다.

---

## 🌿 1. 내 몸을 위한 건강한 선택 (속 편한 베이커리)
- **{usp1}**
- **{usp2}**

소화가 잘되는 천연발효 사워도우라 점심 식사 대용으로도 부담이 없습니다.

---

## ☕ 2. 추천 메뉴 : {hero_name} ({price_str})
바쁜 아침 든든하게 배를 채워주는 {hero_name}.  
아메리카노와의 페어링이 훌륭하여 오후 회의 전 에너지 충전에 제격입니다.

---

## 💡 3. 직장인 알짜 이용 가이드
- **피크타임 대기 안내** : {pain}
- **영업 시간** : {hours}
"""
            cta = f"💼 내일 출근길, {store}에서 갓 구운 빵과 함께 활기찬 하루를 시작해 보세요."

        else:  # LOCAL_FAMILY
            headline = f"우리 가족 안심 먹거리, 정직한 원재료로 굽는 성수동 동네 빵집 '{store}' 🏡"
            body = f"""# [동네 사랑방] 아이와 부모님이 함께 안심하고 찾는 {store}

화려한 기교보다 정직한 원재료와 사람 중심의 온기를 소중히 여기는 공간,  
성수동 이웃 주민들의 따뜻한 쉼터 **'{store}'**입니다.

---

## 🌾 1. 가족의 건강을 생각한 정직한 고집
- **{usp1}**
- **{usp2}**

매일 아침 깨끗한 환경에서 구워내어 어린아이부터 어르신까지 속 편안하게 드실 수 있습니다.

---

## 🍞 2. 온 가족 인기 메뉴 : {hero_name} ({price_str})
자극적이지 않고 담백한 풍미로 아침 식탁을 풍요롭게 채워드립니다.

---

## 🏡 3. 매장 이용 안내
- **안내 사항** : {pain}
- **영업 시간** : {hours}
"""
            cta = f"🌿 이번 주말, 소중한 가족과 함께 {store}의 따뜻한 테라스로 나들이 오세요."

        clean_body = clean_markdown_spacing(body)
        full_text = f"{headline}\n\n{clean_body}\n\n{cta}"
        audit = ComplianceGuard.audit_text(full_text)

        visual_spec = VisualAssetSpec(
            ratio="1:1 (1080x1080px)",
            format_type="감성 카드뉴스 & 인포그래픽",
            layout_description="중앙 갓 구운 단면 클로즈업 + 톤앤매너별 후킹 카피 배치",
            recommended_copy_overlay=f"성수 핫플 {store} 솔직 탐방기!"
        )

        return ChannelContent(
            channel="naver_blog",
            tone=tone,
            headline=headline,
            body=audit.sanitized_text,
            call_to_action=cta,
            hashtags=["#성수동카페", "#성수빵지순례", "#성수핫플", "#사워도우맛집"],
            visual_spec=visual_spec,
            compliance_report=audit,
        )

    # =========================================================================
    # 2. INSTAGRAM GENERATOR (By Tone)
    # =========================================================================
    @classmethod
    def generate_instagram(cls, profile: UnifiedBusinessProfile, tone: str = "MZ_TREND") -> ChannelContent:
        hero = profile.hero_products[0] if profile.hero_products else None
        hero_name = hero.name if hero else "시그니처 디저트"
        store = profile.store_name

        if tone == "MZ_TREND":
            headline = f"🚨 비상 : 빵순이들 지갑 털러 성수동 상륙함 ({store}) 🥐✨"
            body = f"""혈중 버터 농도 긴급 수혈 필요한 사람 손?! 🙋‍♀️✨

프랑스 AOP 버터 들이부은 겉바속촉 끝판왕,
[{hero_name}] 폼 진짜 미쳤음;;

한 입 베어 물면 바사삭 소리에 고막 힐링 🎧
달콤쫀득해서 입안에서 상투스 울림 ㅠㅠ

⚠️ 안내 : 오후 2시면 전량 솔드아웃 실화냐고...
성수 오면 무조건 오픈런 뛰어야 함 🏃‍♂️💨

햇살 좋은 테라스에서 댕댕이랑 브런치 때리면 힐링 그 자체 🐶🤍"""
            cta = "프로필 링크 누르고 오늘의 라인업 & 위치 확인 👆"
            hashtags = [
                "#성수핫플", "#성수동카페", "#빵지순례", "#오픈런맛집",
                "#디저트그램", "#버터바", "#사워도우", "#성수데이트",
                "#힙스터성지", "#댕댕이동반", "#빵순이", "#먹스타그램"
            ]

        elif tone == "WORKER_HEALING":
            headline = f"오늘 하루도 고생한 나를 위한 달콤한 퇴근길 선물 ☕🥐"
            body = f"""반복되는 일상 속, 작은 쉼표가 필요할 때 🌿
성수동 골목 안 향긋한 버터 향 가득한 [{store}]입니다.

풍미 가득한 [{hero_name}]와 따뜻한 라떼 한 잔으로
지친 하루의 스트레스를 가볍게 날려보세요.

오전 11시 전 방문 시 음료 50% 할인 혜택도 놓치지 마세요!"""
            cta = "퇴근길 매장 위치 바로 확인하기 👆"
            hashtags = ["#성수직장인", "#성수동카페", "#퇴근길소확행", "#직장인힐링", "#성수브런치"]

        else:  # LOCAL_FAMILY
            headline = f"우리 가족을 위한 건강하고 속 편한 아침 식탁 🏡🍞"
            body = f"""매일 아침 정성으로 구워내는 성수동 동네 빵집 [{store}]입니다.

100% 천연발효와 엄선된 재료로 만들어
아이들도 어르신도 속 편안하게 드실 수 있는 [{hero_name}].

따뜻한 햇살 드는 야외 테라스에서 온 가족이 여유로운 주말을 즐겨보세요 🤍"""
            cta = "매장 방문 안내 및 예약하기 👆"
            hashtags = ["#성수동맛집", "#가족나들이", "#속편한빵", "#성수베이커리", "#동네사랑방"]

        full_text = f"{headline}\n\n{body}\n\n{cta}"
        audit = ComplianceGuard.audit_text(full_text)

        visual_spec = VisualAssetSpec(
            ratio="1:1 (피드) / 9:16 (릴스 템플릿)",
            format_type="캐러셀 & 무드 숏폼",
            layout_description="슬라이드 1: 햇살 드는 테라스 테이블 연출 컷 / 슬라이드 2~4: 사워도우 쪼개는 3초 모션 컷",
            recommended_copy_overlay="버터 풍미 가득한 성수의 아침 🥐"
        )

        return ChannelContent(
            channel="instagram",
            tone=tone,
            headline=headline,
            body=audit.sanitized_text,
            call_to_action=cta,
            hashtags=hashtags,
            visual_spec=visual_spec,
            compliance_report=audit,
        )

    # =========================================================================
    # 3. KAKAOTALK GENERATOR (By Tone)
    # =========================================================================
    @classmethod
    def generate_kakaotalk(cls, profile: UnifiedBusinessProfile, tone: str = "MZ_TREND") -> ChannelContent:
        promo = profile.active_promotion
        promo_title = promo["title"] if promo else "시즌 스페셜 이벤트"
        promo_benefit = promo["benefit"] if promo else "오전 방문 고객 특별 혜택"
        store = profile.store_name

        if tone == "MZ_TREND":
            headline = f"📢 [단독] {store} 얼리버드 50% 할인 쿠폰 도착 ☕🥐"
            body = f"""{store} 친구들 주목! 👀✨

매일 2시면 품절되는 그 빵집 맞음...
친구들을 위해 특별한 모닝 혜택 준비함!

■ 깜짝 혜택 : {promo_benefit}
■ 이벤트명 : [{promo_title}]
■ 유효기간 : {promo['valid_until'] if promo else '이번 주말까지'}

오전 일찍 와서 갓 구운 빵이랑 커피 반값에 득템해가세요! 🏃‍♀️💨"""
            cta = "👉 반값 할인 쿠폰 받기 & 길찾기"

        elif tone == "WORKER_HEALING":
            headline = f"[힐링 혜택] {store} 출근길 모닝 음료 50% 할인 안내 ☕"
            body = f"""바쁜 출근길, {store}가 따뜻한 응원을 전합니다.

정성껏 구운 사워도우와 함께 든든한 아침을 시작하세요.

■ 직장인 혜택 : {promo_benefit}
■ 행사 기간 : {promo['valid_until'] if promo else '이번 달 말까지'}
■ 매장 위치 : {profile.address}

지친 하루의 시작을 향긋한 커피와 함께 채워보세요."""
            cta = "👉 매장 위치 확인 및 바로 주문하기"

        else:  # LOCAL_FAMILY
            headline = f"[이웃 소식] {store}에서 정성껏 준비한 감사 혜택을 전합니다 🏡"
            body = f"""안녕하세요, {store} 이웃 여러분!

항상 저희 매장을 아껴주시는 고객님들께 보답하고자
소소하지만 따뜻한 나눔 혜택을 준비했습니다.

■ 나눔 혜택 : {promo_benefit}
■ 행사 기간 : {promo['valid_until'] if promo else '이번 달 말까지'}
■ 매장 안내 : {profile.address}

온 가족이 편안한 마음으로 들러 따뜻한 온기를 나누어 보세요."""
            cta = "👉 매장 길찾기 및 단골 혜택 확인"

        full_text = f"{headline}\n\n{body}\n\n{cta}"
        audit = ComplianceGuard.audit_text(full_text)

        visual_spec = VisualAssetSpec(
            ratio="4:3 (800x600px 와이드 배너)",
            format_type="와이드 클릭형 배너",
            layout_description="좌측 볼드 타이포 '[50% 할인]' 뱃지 + 우측 라떼와 사워도우 따뜻한 톤앤매너 이미지",
            recommended_copy_overlay="오전 11시 전 방문 시 아메리카노 반값!"
        )

        return ChannelContent(
            channel="kakaotalk",
            tone=tone,
            headline=headline,
            body=audit.sanitized_text,
            call_to_action=cta,
            hashtags=[],
            visual_spec=visual_spec,
            compliance_report=audit,
        )

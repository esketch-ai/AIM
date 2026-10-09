"""AIM (AI Platform Initiative) - Multi-Channel & Multi-Tone Content Generator
Supports targeted audience tones:
1. MZ_TREND: 2030 Hipster, Dopamine-hooking, Short-form, Witty Slangs & Emojis
2. WORKER_HEALING: 3040 Busy Workers, Stress Relief, Practical Coffee/Brunch Tips
3. LOCAL_FAMILY: 4050+ Neighborhood Families, Clean/Healthy Ingredients, Trust & Warmth
"""

import re
from typing import Dict, Any
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

    # =========================================================================
    # 4. YOUTUBE SHORTS GENERATOR (By Tone) - docs/AIM_Base.md §2.④
    # =========================================================================
    @classmethod
    def generate_youtube_shorts(cls, profile: UnifiedBusinessProfile, tone: str = "MZ_TREND") -> ChannelContent:
        hero = profile.hero_products[0] if profile.hero_products else None
        hero_name = hero.name if hero else "시그니처 바질 소금빵"
        store = profile.store_name
        usp1 = profile.core_usps[0] if profile.core_usps else "프랑스 AOP 고메버터 48% 함유"
        pain = profile.pain_points[0] if profile.pain_points else "오후 2시 전량 품절 주의"

        if tone == "MZ_TREND":
            headline = f"오후 2시 품절 실화?! 성수동 빵순이 오픈런 솔직 리뷰 ({store}) 🥐💥"
            body = f"""【30초 내레이션 타임스탬프 스크립트】
[00:00 - 00:03 오프닝 후킹]
"성수동에서 오후 2시만 되면 싹 쓸려나가는 이 빵, 대체 정체가 뭘까요?"

[00:03 - 00:10 문제 제기 & 현장 분위기]
"매일 오픈 전부터 줄 선다는 {store}! 버터 냄새에 홀려서 저도 오픈런 뛰어봤습니다."

[00:10 - 00:22 핵심 USP & 감각적 묘사]
"바로 이 {hero_name}! 겉은 파사삭 부서지는데, 속은 {usp1}로 촉촉 쫀득함 그 자체! 한 입 베어 물면 버터 풍미가 입안 가득 터져나옵니다."

[00:22 - 00:30 결론 & 방문 CTA]
"단, {pain}! 고소한 버터 폭탄 맞고 싶다면 지금 바로 성수동으로 달려가세요!"
"""
            cta = "고정 댓글 링크 클릭하고 오늘 남은 수량 & 할인 쿠폰 확인 👆"
            hashtags = ["#쇼츠", "#성수동핫플", "#빵지순례", "#오픈런", "#바질소금빵", "#디저트맛집"]
        elif tone == "WORKER_HEALING":
            headline = f"퇴근길 30초 힐링 : 지친 나를 위로하는 갓 구운 {hero_name} ({store}) ☕"
            body = f"""【30초 내레이션 타임스탬프 스크립트】
[00:00 - 00:03 오프닝 후킹]
"오늘 하루도 야근에 치여 방전되셨나요? 30초만 눈 감고 버터 향을 맡아보세요."

[00:03 - 00:10 공감 & 공간 소개]
"성수동 골목 안 조용한 쉼터, {store}. 문을 열자마자 퍼지는 고소한 온기."

[00:10 - 00:22 메뉴 힐링 포인트]
"속 편한 천연발효 사워도우와 {hero_name}. 따뜻한 라떼 한 모금과 곁들이면 오늘 쌓인 피로가 사르르 녹아내립니다."

[00:22 - 00:30 행동 촉구]
"수고한 나를 위한 작은 보상, 오늘 퇴근길에 들러보세요."
"""
            cta = "퇴근길 매장 위치 및 실시간 길찾기 👆"
            hashtags = ["#성수직장인", "#퇴근길소확행", "#힐링디저트", "#성수카페", "#베이커리쇼츠"]
        else:  # LOCAL_FAMILY
            headline = f"아이와 함께 안심하고 먹는 우리 동네 건강한 빵집 ({store}) 🏡🍞"
            body = f"""【30초 내레이션 타임스탬프 스크립트】
[00:00 - 00:03 오프닝 후킹]
"매일 아침 아이 식탁에 올리는 빵, 어떤 원재료로 만들어졌는지 확인해보셨나요?"

[00:03 - 00:10 정직한 생산 과정]
"성수동 이웃들의 건강을 생각하는 {store}. 매일 새벽 정직하게 반죽합니다."

[00:10 - 00:22 건강한 식재료]
"인공첨가물 없이 {usp1}. 어린아이부터 부모님까지 속 편안하게 즐길 수 있는 {hero_name}입니다."

[00:22 - 00:30 이웃 방문 안내]
"이번 주말, 온 가족이 함께 따뜻한 테라스로 나들이 오세요."
"""
            cta = "동네 사랑방 매장 위치 & 가족 테이블 예약 👆"
            hashtags = ["#동네빵집", "#속편한빵", "#가족나들이", "#성수동베이커리", "#건강한간식"]

        full_text = f"{headline}\n\n{body}\n\n{cta}"
        audit = ComplianceGuard.audit_text(full_text)

        visual_spec = VisualAssetSpec(
            ratio="9:16 (1080x1920px 세로형 숏폼)",
            format_type="유튜브 쇼츠 & 틱톡 타임라인 템플릿",
            layout_description="상단 고CTR 자막 바 + 중앙 빵 커팅 3초 모션 슬로우 줌인 + 하단 15초 바코드 오버레이",
            recommended_copy_overlay=f"오후 2시 품절각?! {hero_name} 솔직 후기"
        )

        return ChannelContent(
            channel="youtube_shorts",
            tone=tone,
            headline=headline,
            body=audit.sanitized_text,
            call_to_action=cta,
            hashtags=hashtags,
            visual_spec=visual_spec,
            compliance_report=audit,
        )

    # =========================================================================
    # 5. COMMERCE DETAIL PAGE GENERATOR (By Tone) - docs/AIM_Base.md §2.⑤
    # =========================================================================
    @classmethod
    def generate_commerce_detail(cls, profile: UnifiedBusinessProfile, tone: str = "MZ_TREND") -> ChannelContent:
        hero = profile.hero_products[0] if profile.hero_products else None
        hero_name = hero.name if hero else "시그니처 바질 소금빵"
        price_str = f"{hero.unit_price:,}원" if hero else "4,500원"
        store = profile.store_name
        usp1 = profile.core_usps[0] if profile.core_usps else "프랑스 AOP 고메버터 48% 함유"
        usp2 = profile.core_usps[1] if len(profile.core_usps) > 1 else "당일 새벽 반죽 당일 출고 원칙"

        headline = f"[스마트스토어/쿠팡] {store} 프리미엄 수제 {hero_name} ({price_str}) 모바일 상세페이지"
        body = f"""# 【{store}】 프리미엄 {hero_name}

## 🌟 1. 왜 {store}의 {hero_name}인가요? (핵심 소구점)
- **독보적 원재료** : {usp1}로 겉은 바삭하고 속은 쫀득 고소한 프리미엄 풍미.
- **철저한 원칙** : {usp2}으로 신선함이 살아있는 살아 숨 쉬는 식감.
- **검증된 만족도** : 매장 방문 고객 평점 4.9점 / 2만 개 누적 리뷰 입증!

---

## 📦 2. 구매 전 가장 많이 묻는 질문 FAQ (우려 해소)
**Q1. 보관 및 가장 맛있게 먹는 방법은 무엇인가요?**
A. 수령 당일 드시는 것이 가장 맛있으며, 남은 제품은 밀폐 후 냉동 보관(최대 30일)하세요. 에어프라이어 180℃에서 3분간 데우면 갓 구운 바삭함을 그대로 즐기실 수 있습니다.

**Q2. 당일 생산 제품이 맞나요?**
A. 네, 100% 당일 새벽 반죽 및 당일 구운 제품만 엄선하여 발송합니다. 재고 판매는 절대 하지 않습니다.

**Q3. 배송 중 파손이나 신선도 저하 우려는 없나요?**
A. 친환경 전용 항온 아이스박스와 에어캡 완충 포장으로 매장에서 갓 나온 신선도 그대로 안전하게 문 앞까지 배송됩니다.

---

## 🏷️ 3. 제품 사양 및 인증 정보
- **내용량** : 개당 85g ± 5g
- **보관방법** : 실온 2일 / 냉동 30일
- **원산지** : 프랑스산 고메버터, 국산 유기농 밀가루
"""
        cta = "지금 바로 구매하기 (당일 오후 2시 이전 주문 시 당일 발송) ➔"
        full_text = f"{headline}\n\n{body}\n\n{cta}"
        audit = ComplianceGuard.audit_text(full_text)

        visual_spec = VisualAssetSpec(
            ratio="모바일 최적화 (가로 860px 세로형 상세 블록)",
            format_type="이커머스 상세페이지 블록 & 스펙 비교표",
            layout_description="블록 1: 원물 버터 단면 스팀 컷 / 블록 2: 3대 안심 보증 배지 / 블록 3: 에어프라이어 3분 꿀팁",
            recommended_copy_overlay=f"당일 구워 당일 출발! {store} {hero_name}"
        )

        return ChannelContent(
            channel="commerce_detail",
            tone=tone,
            headline=headline,
            body=audit.sanitized_text,
            call_to_action=cta,
            hashtags=["#스마트스토어", "#산지직송", "#수제베이커리", "#홈카페"],
            visual_spec=visual_spec,
            compliance_report=audit,
        )

    # =========================================================================
    # 6. AEO / GEO SCHEMA.ORG JSON-LD GENERATOR - docs/03 §1.①
    # =========================================================================
    @classmethod
    def generate_geo_schema_jsonld(cls, profile: UnifiedBusinessProfile, target_engine: str = "ALL") -> Dict[str, Any]:
        """Generates Schema.org compliant JSON-LD structured data for Generative Engine Optimization (GEO).

        Enables ChatGPT, Perplexity, Google SGE, and Naver Cue to reliably cite store data,
        USPs, menus, operating hours, and promotions in AI generated answers.
        """
        hero = profile.hero_products[0] if profile.hero_products else None
        hero_name = hero.name if hero else "시그니처 메뉴"
        price_val = hero.unit_price if hero else 4500

        schema = {
            "@context": "https://schema.org",
            "@type": "Bakery",
            "name": profile.store_name,
            "description": f"{profile.store_name} - {profile.core_usps[0] if profile.core_usps else '정통 수제 베이커리'}",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": profile.address,
                "addressLocality": "Seoul",
                "addressCountry": "KR",
            },
            "openingHours": profile.business_hours,
            "servesCuisine": "Bakery, Specialty Coffee, French Pastry",
            "priceRange": "₩₩",
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": "시그니처 메뉴 라인업",
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "itemOffered": {
                            "@type": "MenuItem",
                            "name": p.name,
                            "description": f"인기 메뉴 {p.name}",
                        },
                        "price": p.unit_price,
                        "priceCurrency": "KRW",
                    }
                    for p in profile.hero_products
                ],
            },
            "faqPage": {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"{profile.store_name}의 대표 시그니처 메뉴는 무엇인가요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"대표 메뉴는 {hero_name}이며, 가격은 {price_val:,}원입니다. {profile.core_usps[0] if profile.core_usps else '당일 생산'}",
                        },
                    },
                    {
                        "@type": "Question",
                        "name": f"{profile.store_name}의 영업 시간 및 웨이팅 안내는 어떻게 되나요?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"영업 시간은 {profile.business_hours}이며, {profile.pain_points[0] if profile.pain_points else '오후 조기 품절될 수 있습니다.'}",
                        },
                    },
                ],
            },
        }

        if profile.active_promotion:
            schema["specialAnnouncement"] = {
                "@type": "SpecialAnnouncement",
                "name": profile.active_promotion.get("title", "특별 프로모션"),
                "text": profile.active_promotion.get("benefit", "할인 혜택"),
                "expires": profile.active_promotion.get("valid_until", "2026-12-31"),
            }

        return schema

    # =========================================================================
    # 7. 5-CHANNEL ATOMIZATION BUNDLER - docs/AIM_Base.md §2
    # =========================================================================
    @classmethod
    def generate_all_5channels(cls, profile: UnifiedBusinessProfile, tone: str = "MZ_TREND") -> Dict[str, ChannelContent]:
        """Atomizes Single Source of Truth into all 5 canonical marketing channels."""
        return {
            "naver_blog": cls.generate_naver_blog(profile, tone=tone),
            "kakaotalk": cls.generate_kakaotalk(profile, tone=tone),
            "instagram": cls.generate_instagram(profile, tone=tone),
            "youtube_shorts": cls.generate_youtube_shorts(profile, tone=tone),
            "commerce_detail": cls.generate_commerce_detail(profile, tone=tone),
        }


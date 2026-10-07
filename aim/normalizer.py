"""AIM (AI Platform Initiative) - Normalizer & Single Source Engine
Converts raw heterogeneous store data (POS, receipt reviews, QnA) into a clean,
PII-masked, normalized UnifiedBusinessProfile (Single Source of Truth).
"""

import re
from typing import List, Tuple
from aim.schema import (
    RawStoreData,
    RawReview,
    NormalizedProduct,
    UnifiedBusinessProfile,
)


def mask_pii(text: str) -> str:
    """Masks Personally Identifiable Information (phone numbers, emails) from raw text."""
    # Phone numbers (e.g. 010-1234-5678, 010.1234.5678, 02-123-4567)
    phone_pattern = r"(01[0-9][-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4}|0[2-6][0-9]?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4})"
    text = re.sub(phone_pattern, "[연락처 마스킹]", text)

    # Email addresses
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    text = re.sub(email_pattern, "[이메일 마스킹]", text)

    # Clean author names if embedded
    text = re.sub(r"\([고객|user].*?\)", "", text)
    return text.strip()


def extract_customer_signals(reviews: List[RawReview]) -> Tuple[List[str], List[str], List[str]]:
    """Analyzes customer reviews to extract positive highlights, pain points, and context tags.
    In production, this is augmented with an NLP sentiment classifier.
    Here we provide a deterministic, zero-hallucination baseline.
    """
    positive_signals = []
    pain_points = []
    context_tags = set()

    positive_keywords = {
        "겉바속촉": "바삭하고 촉촉한 정통 식감 호평",
        "버터 풍미": "AOP 버터 특유의 깊은 풍미 만족",
        "테라스": "반려동물 동반 가능한 테라스 환경 만족",
        "재구매": "높은 재구매 만족도 및 선물 추천",
        "포장 꼼꼼": "온라인 배송 및 테이크아웃 포장 품질 우수"
    }

    pain_keywords = {
        "품절": "인기 품목(사워도우) 조기 품절로 인한 헛걸음 방지 안내 필요",
        "주차": "매장 인근 주차 공간 협소 안내 및 대중교통/도보 방문 권장 필요",
        "웨이팅": "피크 타임 대기 시간 안내 및 네이버 예약 연동 필요"
    }

    for rev in reviews:
        clean_text = mask_pii(rev.text)
        
        for kw, desc in positive_keywords.items():
            if kw in clean_text and desc not in positive_signals:
                positive_signals.append(desc)
                
        for kw, desc in pain_keywords.items():
            if kw in clean_text and desc not in pain_points:
                pain_points.append(desc)

        # Context tag derivation
        if "강아지" in clean_text or "테라스" in clean_text:
            context_tags.add("#반려동물동반")
        if "택배" in clean_text or "스마트스토어" in rev.source:
            context_tags.add("#전국택배배송")
        if "성수" in clean_text or "직장인" in clean_text:
            context_tags.add("#성수핫플디저트")

    return positive_signals, pain_points, sorted(list(context_tags))


class StoreDataNormalizer:
    """Normalizes raw heterogeneous store data into Single Source of Truth."""

    @classmethod
    def normalize(cls, raw: RawStoreData) -> UnifiedBusinessProfile:
        pos = raw.pos_summary
        store = raw.store_info

        # 1. Transform POS products into Hero products
        hero_products = []
        for item in pos.top_selling_items:
            highlights = []
            if pos.low_stock_risk_item and item.item_name in pos.low_stock_risk_item:
                highlights.append("인기 폭발 당일 한정 조기 마감 품목")
            if item.sales_count >= 500:
                highlights.append(f"월간 누적 {item.sales_count:,}개 판매 베스트셀러")

            hero_products.append(
                NormalizedProduct(
                    name=item.item_name,
                    sales_volume_desc=f"월 {item.sales_count:,}건 판매",
                    unit_price=item.unit_price,
                    highlights=highlights,
                )
            )

        # 2. Extract customer signals from reviews
        pos_signals, pains, tags = extract_customer_signals(raw.raw_reviews)

        # 3. Format active promotion
        active_promo = None
        if raw.current_promotions:
            p = raw.current_promotions[0]
            active_promo = {
                "title": p.title,
                "benefit": p.benefit,
                "valid_until": p.valid_until,
            }

        return UnifiedBusinessProfile(
            store_id=store.store_id,
            store_name=store.name,
            category=store.category,
            address=store.address,
            business_hours=store.business_hours,
            core_usps=store.usp_highlights,
            hero_products=hero_products,
            positive_signals=pos_signals,
            pain_points=pains,
            context_tags=tags,
            active_promotion=active_promo,
        )

"""AIM (AI Platform Initiative) - Reputation & Crisis Defense Engine
Detects negative / 1-star reviews and generates 3-tier dignified crisis responses:
1. Empathetic Apology & Swift Action (정중 사과 & 신속 조치)
2. Factual Clarification & Reassurance (팩트 정정 & 오해 해소)
3. Retention Recovery & Hospitality (재방문 유도 & 온정 보상)
"""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel
from aim.compliance import ComplianceGuard


class ReviewComplaintAnalysis(BaseModel):
    rating: float
    sentiment: str  # 'CRITICAL_NEGATIVE', 'MILD_NEGATIVE', 'POSITIVE'
    complaint_type: str  # 'SERVICE_ATTITUDE', 'FOOD_QUALITY', 'WAIT_TIME', 'DELIVERY_PACKAGING', 'GENERAL'
    key_issue_phrases: List[str]


class CrisisResponseOptions(BaseModel):
    store_name: str
    original_review: str
    analysis: ReviewComplaintAnalysis
    option_empathetic: str  # Option 1: 공감 사과형
    option_factual: str     # Option 2: 팩트 설명형
    option_recovery: str    # Option 3: 재방문 케어형
    compliance_safe: bool


class ReputationCrisisEngine:
    """Safeguards local business reputation against malicious or negative 1-star reviews."""

    COMPLAINT_PATTERNS = {
        "SERVICE_ATTITUDE": ["불친절", "화내", "인상", "말투", "태도", "무시"],
        "FOOD_QUALITY": ["맛없", "비려", "짜", "싱거", "덜익", "상했", "식었", "딱딱"],
        "WAIT_TIME": ["늦게", "웨이팅", "대기", "한참", "안나와", "오래걸"],
        "DELIVERY_PACKAGING": ["새어", "터졌", "쏟아", "포장", "배달"],
    }

    @classmethod
    def analyze_review(cls, text: str, rating: float = 1.0) -> ReviewComplaintAnalysis:
        detected_type = "GENERAL"
        matched_phrases = []

        for comp_type, keywords in cls.COMPLAINT_PATTERNS.items():
            for kw in keywords:
                if kw in text:
                    detected_type = comp_type
                    matched_phrases.append(kw)

        if rating <= 2.0:
            sentiment = "CRITICAL_NEGATIVE"
        elif rating <= 3.5:
            sentiment = "MILD_NEGATIVE"
        else:
            sentiment = "POSITIVE"

        return ReviewComplaintAnalysis(
            rating=rating,
            sentiment=sentiment,
            complaint_type=detected_type,
            key_issue_phrases=matched_phrases or ["일반 이용 불편"],
        )

    @classmethod
    def generate_dignified_responses(
        cls, store_name: str, review_text: str, rating: float = 1.0
    ) -> CrisisResponseOptions:
        analysis = cls.analyze_review(review_text, rating)

        # 1. Option 1: Empathetic Apology & Immediate Improvement
        opt1 = (
            f"안녕하세요, {store_name} 대표입니다.\n"
            f"먼저 소중한 걸음으로 저희 매장을 찾아주셨음에도 불구하고, 마음 상하게 해 드려 진심으로 고개 숙여 사과드립니다.\n"
            f"남겨주신 불편 사항({', '.join(analysis.key_issue_phrases)})은 저희 팀 전체가 무겁게 받아들이고 즉각 전면 재점검을 진행하였습니다.\n"
            f"앞으로 찾아주시는 모든 분들께 한결같이 편안하고 만족스러운 경험만을 드릴 수 있도록 기본부터 다시 철저히 챙기겠습니다.\n"
            f"다시 한번 귀한 시간 내어 소중한 쓴소리 남겨주셔서 깊이 감사드립니다."
        )

        # 2. Option 2: Factual Clarification & Reassurance (For other prospective customers)
        opt2 = (
            f"안녕하세요, {store_name}입니다.\n"
            f"우선 고객님께서 이용 중 겪으신 불편에 대해 송구스러운 마음을 전합니다.\n"
            f"저희 매장은 당일 생산 원칙과 엄선된 레시피를 기반으로 운영되고 있으나, 고객님께서 느끼신 아쉬운 부분에 대해 부족한 점이 있었는지 세심하게 살펴보았습니다.\n"
            f"말씀해 주신 피드백을 토대로 조리 공정과 매장 응대 프로세스를 보완하여 한 분 한 분께 정성을 다하는 공간이 되겠습니다.\n"
            f"소중한 의견 감사드리며, 더욱 신뢰받는 {store_name}가 되겠습니다."
        )

        # 3. Option 3: Retention Recovery & Hospitality Care
        opt3 = (
            f"안녕하세요, {store_name} 점장입니다.\n"
            f"기대하고 찾아주셨을 텐데 흡족한 시간을 선물해 드리지 못해 죄송하고 무거운 마음입니다.\n"
            f"부족했던 부분에 대해 깊이 반성하며, 기회를 주신다면 고객님께 꼭 만족스러운 대접으로 보답하고 싶습니다.\n"
            f"매장으로 편안한 시간대에 연락(또는 재방문 시 대표를 찾아주시면) 주시면, 정성을 다해 다시 모시겠습니다.\n"
            f"환절기 건강 유의하시고, 항상 평안하시길 바랍니다."
        )

        # Audit with compliance guard
        all_safe = all(
            ComplianceGuard.audit_text(t).is_compliant for t in [opt1, opt2, opt3]
        )

        return CrisisResponseOptions(
            store_name=store_name,
            original_review=review_text,
            analysis=analysis,
            option_empathetic=opt1,
            option_factual=opt2,
            option_recovery=opt3,
            compliance_safe=all_safe,
        )

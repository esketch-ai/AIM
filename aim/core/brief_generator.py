"""
AIM Standardized Brief Generator (aim/core/brief_generator.py)
--------------------------------------------------------------
Generates a 1-page standardized creator brief from 3 essential merchant questions:
Q1: Product/service to sell
Q2: Single core benefit the customer experiences
Q3: Target customer demographic and situation
+ Format & budget tier tagging.
"""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from aim.core.value_compressor import ValueCompressor, ValueCompressionRequest


class BriefQuestionnaireInput(BaseModel):
    product_name: str = Field(..., description="Q1: 오늘 가장 알리고 싶은 상품/서비스")
    core_benefit: str = Field(..., description="Q2: 손님이 경험할 단 하나의 핵심 이득")
    target_audience: str = Field(..., description="Q3: 우리 손님의 주 연령/성별/상황")
    content_format: str = Field(default="SHORTS", description="SHORTS, REELS, TIKTOK, LIVE_COMMERCE")
    budget_tier: str = Field(default="MID_450K", description="MICRO_150K, MID_450K, PRO_900K")
    industry: str = Field(default="FNB", description="FNB, BEAUTY, MEDICAL, B2B_SAAS, MANUFACTURING")
    tenant_id: Optional[str] = Field(None, description="Requesting merchant tenant ID")


class StoryboardScene(BaseModel):
    scene_number: int
    duration_seconds: int
    visual_cue: str
    audio_narration: str
    overlay_text: str


class StandardizedCreatorBrief(BaseModel):
    brief_id: str
    title: str
    content_format: str
    budget_tier: str
    industry: str
    hooking_copy: str
    scenes: List[StoryboardScene]
    dos_and_donts: Dict[str, List[str]]
    compliance_guidelines: List[str]
    sla_notice: str
    summary_for_creator: str


class BriefGenerator:
    """Generates ready-to-produce 15~30s short-form creator briefs."""

    FORMAT_SPECS = {
        "SHORTS": {"name": "YouTube Shorts (9:16 세로형, 15~30초)", "aspect": "9:16"},
        "REELS": {"name": "Instagram Reels (9:16 세로형, 15~30초)", "aspect": "9:16"},
        "TIKTOK": {"name": "TikTok (9:16 세로형, 15초 템포)", "aspect": "9:16"},
        "LIVE_COMMERCE": {"name": "네이버 쇼핑라이브 (60분 실시간)", "aspect": "9:16"},
    }

    BUDGET_RATES = {
        "MICRO_150K": {"amount": 150000, "label": "마이크로 (15만원, 팔로워 5천~2만)"},
        "MID_450K": {"amount": 450000, "label": "미드 티어 (45만원, 팔로워 3만~10만)"},
        "PRO_900K": {"amount": 900000, "label": "프로 파워 (90만원, 팔로워 10만+)"},
    }

    def __init__(self):
        self.compressor = ValueCompressor()

    def generate(self, inp: BriefQuestionnaireInput) -> StandardizedCreatorBrief:
        brief_id = f"BRIEF_{uuid.uuid4().hex[:8].upper()}"

        # 1. Generate compressed hook and pitch
        comp_req = ValueCompressionRequest(
            product_name=inp.product_name,
            raw_benefit=inp.core_benefit,
            target_audience=inp.target_audience,
            industry=inp.industry,
        )
        compressed = self.compressor.compress(comp_req)

        format_info = self.FORMAT_SPECS.get(inp.content_format, self.FORMAT_SPECS["SHORTS"])
        budget_info = self.BUDGET_RATES.get(inp.budget_tier, self.BUDGET_RATES["MID_450K"])

        # 2. 15-second Storyboard generation (Hook -> Pain -> Solution -> CTA)
        scenes = [
            StoryboardScene(
                scene_number=1,
                duration_seconds=3,
                visual_cue=f"시선 집중 0.5초 컷. {inp.product_name}의 극적인 첫인상 클로즈업.",
                audio_narration=compressed.pain_point_strike,
                overlay_text=f"🚨 {compressed.pain_point_strike[:18]}...",
            ),
            StoryboardScene(
                scene_number=2,
                duration_seconds=4,
                visual_cue="타깃 고객의 답답한 일상과 제품의 극명한 대비 컷.",
                audio_narration=f"{inp.target_audience}라면 매일 겪는 이 고민, 해결책은 딱 하나입니다.",
                overlay_text=f"👉 {inp.target_audience} 집중!",
            ),
            StoryboardScene(
                scene_number=3,
                duration_seconds=5,
                visual_cue=f"실제 소비/체험 현장. {inp.product_name}의 질감, 소리, 속도감을 극대화한 비주얼.",
                audio_narration=compressed.metaphor_and_number,
                overlay_text=f"✨ {inp.core_benefit[:20]}",
            ),
            StoryboardScene(
                scene_number=4,
                duration_seconds=3,
                visual_cue="단일 행동 유도 화면. 프로필 링크 또는 고정 댓글 쿠폰 바코드 안내.",
                audio_narration=f"{compressed.direct_cta}! 지금 프로필 링크를 확인하세요.",
                overlay_text=f"🎁 {compressed.direct_cta}",
            ),
        ]

        # 3. Industry-specific compliance & Do's/Don'ts
        compliance_list = [
            "공정거래위원회 추천·보증 심사지침 준수: 영상 첫 화면 및 더보기란에 '유료 광고 포함' 자막 필수 표기",
            "허위·과장 광고 금지: 객관적 근거 없는 '국내 최초', '세계 1위' 절대 사용 불가",
        ]
        if inp.industry == "MEDICAL":
            compliance_list.append("의료법 제56조 준수: 치료경험담(후기성 표현) 금지, 시술 전후 비교사진 단독 사용 금지, 부작용 경고 문구 필수")

        dos_and_donts = {
            "DO (필수 연출)": [
                "첫 3초 안에 제품 실물과 핵심 카피 동시 노출",
                "ASMR 또는 현장 사운드(바삭거리는 소리, 시술 기기 작동음)를 생생하게 수음",
                "고정 댓글에 제공된 단일 단축 URL/쿠폰 코드 정확히 삽입",
            ],
            "DONT (절대 금지)": [
                "지루한 매장 외관/간판 5초 이상 비추기 금지",
                "제공된 가이드 외 경쟁사 비방 및 비식별 비하 발언 금지",
                "광고 표기를 영상 뒤쪽에 숨겨 배치하는 행위 금지",
            ],
        }

        sla_notice = (
            "⚡ 24h Fast-Track 검수 SLA: 크리에이터 초안 업로드 후 24시간 이내 사업주 승인 원칙. "
            "수정 요청은 표준 약관상 1회로 제한되며, 24시간 무응답 시 자동 승인 및 에스크로 정산 확정."
        )

        title = f"[{format_info['name']}] {inp.product_name} — 15초 초압축 바이럴 브리프"
        summary = (
            f"타깃: {inp.target_audience} | 포맷: {inp.content_format} | 예산: {budget_info['label']}\n"
            f"핵심 후킹: \"{compressed.pain_point_strike}\"\n"
            f"단일 CTA: \"{compressed.direct_cta}\""
        )

        return StandardizedCreatorBrief(
            brief_id=brief_id,
            title=title,
            content_format=inp.content_format,
            budget_tier=inp.budget_tier,
            industry=inp.industry,
            hooking_copy=compressed.pain_point_strike,
            scenes=scenes,
            dos_and_donts=dos_and_donts,
            compliance_guidelines=compliance_list,
            sla_notice=sla_notice,
            summary_for_creator=summary,
        )

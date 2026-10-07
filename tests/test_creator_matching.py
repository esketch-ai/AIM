"""
Test Suite for AIM Value Compression & Creator On-Demand Matching Marketplace
Tests:
1. ValueCompressor 3-principle output (Pain-Point, Hard Numbers, Single CTA)
2. BriefGenerator 3-question input to 15s structured storyboard and SLA
3. CreatorNetwork matching algorithm, demographics affinity, ranking
4. Escrow fee calculation (10% subscriber discount vs 15% standard)
5. 24h Fast-Track review lifecycle and 1-revision SLA guardrail
6. REST API endpoints in creator_router
"""

import pytest
from fastapi.testclient import TestClient

from aim.core.value_compressor import ValueCompressor, ValueCompressionRequest
from aim.core.brief_generator import BriefGenerator, BriefQuestionnaireInput
from aim.matching.creator_network import (
    CreatorNetwork,
    MatchRequest,
)
from aim.web_app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_value_compressor_principles():
    compressor = ValueCompressor()
    req = ValueCompressionRequest(
        product_name="시그니처 바질 소금빵",
        raw_benefit="프랑스산 고메버터 48%로 구워내 풍미가 진하고 바삭함",
        target_audience="오후 3시 성수동 직장인",
        pain_point="나른한 오후, 눅눅한 빵에 실망하셨나요?",
        action_type="DISCOUNT_COUPON",
        industry="FNB",
    )
    res = compressor.compress(req)

    assert "나른한 오후, 눅눅한 빵에 실망하셨나요?" in res.pain_point_strike
    assert "버터 함량 48%" in res.metaphor_and_number
    assert "원클릭 타임어택 쿠폰" in res.direct_cta
    assert res.hook_duration_seconds == 3
    assert res.total_pitch_seconds == 15
    assert res.retention_score >= 90.0


def test_brief_generator_3_questions_to_storyboard():
    generator = BriefGenerator()
    inp = BriefQuestionnaireInput(
        product_name="시그니처 바질 소금빵",
        core_benefit="오후 3시 나른한 시간, 버터 풍미 가득한 바삭한 힐링",
        target_audience="2030 성수동 직장인 및 디저트 러버",
        content_format="SHORTS",
        budget_tier="MID_450K",
        industry="FNB",
    )
    brief = generator.generate(inp)

    assert brief.brief_id.startswith("BRIEF_")
    assert "YouTube Shorts" in brief.title
    assert len(brief.scenes) == 4  # 4 scenes: Hook, Pain, Solution, CTA
    assert brief.scenes[0].scene_number == 1
    assert brief.scenes[0].duration_seconds == 3
    assert "DO (필수 연출)" in brief.dos_and_donts
    assert "DONT (절대 금지)" in brief.dos_and_donts
    assert any("공정거래위원회" in c for c in brief.compliance_guidelines)
    assert "24h Fast-Track" in brief.sla_notice


def test_brief_generator_medical_compliance():
    generator = BriefGenerator()
    inp = BriefQuestionnaireInput(
        product_name="스킨부스터 리프팅",
        core_benefit="피부 속건조 즉각 해결 및 콜라겐 활성화",
        target_audience="환절기 건조함에 시달리는 3040 직장인",
        content_format="REELS",
        budget_tier="PRO_900K",
        industry="MEDICAL",
    )
    brief = generator.generate(inp)

    assert any("의료법 제56조" in c for c in brief.compliance_guidelines)


def test_creator_matching_algorithm_and_subscriber_discount():
    network = CreatorNetwork()
    # Match for FNB with PRO subscription
    req = MatchRequest(
        category="FNB",
        content_format="SHORTS",
        budget_tier="MID_450K",
        target_audience="2030 여성 성수동",
        subscriber_plan="PRO",
    )
    matches = network.match_creators(req)

    assert len(matches) > 0
    top_match = matches[0]
    assert top_match.creator.category == "FNB"
    assert top_match.match_score >= 80.0
    assert top_match.take_rate_pct == 10.0  # 10% subscriber discount applied

    # Match for Free / non-subscriber
    req_free = MatchRequest(
        category="FNB",
        content_format="SHORTS",
        budget_tier="MID_450K",
        target_audience="2030 여성 성수동",
        subscriber_plan="FREE",
    )
    matches_free = network.match_creators(req_free)
    assert matches_free[0].take_rate_pct == 15.0  # 15% standard rate


def test_escrow_order_locking_and_24h_fast_track_review():
    network = CreatorNetwork()
    deal = network.create_escrow_deal(
        tenant_id="TENANT_001",
        creator_id="CR_FNB_02",
        brief_id="BRIEF_TEST_01",
        subscriber_plan="PRO",
    )

    assert deal.deal_id.startswith("DEAL_")
    assert deal.status == "ESCROW_LOCKED"
    assert deal.total_budget == 450000
    assert deal.take_rate_pct == 10.0
    assert deal.platform_fee == 45000
    assert deal.creator_total_fee == 405000
    assert deal.creator_base_payout == int(405000 * 0.70)
    assert deal.creator_bonus_payout == 405000 - int(405000 * 0.70)

    # Approve deal
    approved = network.review_deal(deal.deal_id, action="APPROVE")
    assert approved.status == "APPROVED"

    # Revision test with max 1 SLA limit
    deal2 = network.create_escrow_deal("TENANT_002", "CR_BEAUTY_01", "BRIEF_02", "PRO")
    revised = network.review_deal(deal2.deal_id, action="REVISE", feedback="후킹 1초 단축 요망")
    assert revised.status == "REVISION_REQUESTED"
    assert revised.revision_count == 1

    # Second revision should fail per SLA rule
    with pytest.raises(ValueError, match="1회를 초과하는 수정"):
        network.review_deal(deal2.deal_id, action="REVISE", feedback="재수정 요청")


def test_api_creator_endpoints(client):
    # 1. Test value compression API
    comp_res = client.post(
        "/api/v1/creator/value/compress",
        json={
            "product_name": "바질 소금빵",
            "raw_benefit": "프랑스산 고메버터 48%",
            "target_audience": "2030 직장인",
            "industry": "FNB",
        },
    )
    assert comp_res.status_code == 200
    assert "pain_point_strike" in comp_res.json()

    # 2. Test brief generate API
    brief_res = client.post(
        "/api/v1/creator/brief/generate",
        json={
            "product_name": "바질 소금빵",
            "core_benefit": "바삭한 버터 풍미",
            "target_audience": "성수동 직장인",
            "content_format": "SHORTS",
            "budget_tier": "MID_450K",
            "industry": "FNB",
        },
    )
    assert brief_res.status_code == 200
    brief_data = brief_res.json()
    assert len(brief_data["scenes"]) == 4

    # 3. Test matching API
    match_res = client.post(
        "/api/v1/creator/match",
        json={
            "category": "FNB",
            "content_format": "SHORTS",
            "budget_tier": "MID_450K",
            "target_audience": "2030 직장인",
            "subscriber_plan": "PRO",
        },
    )
    assert match_res.status_code == 200
    assert match_res.json()["subscriber_discount_applied"] is True
    assert len(match_res.json()["creators"]) > 0

    # 4. Test escrow order API
    order_res = client.post(
        "/api/v1/creator/escrow/order",
        json={
            "tenant_id": "TENANT_001",
            "creator_id": "CR_FNB_01",
            "brief_id": brief_data["brief_id"],
            "subscriber_plan": "PRO",
        },
    )
    assert order_res.status_code == 200
    assert order_res.json()["deal"]["status"] == "ESCROW_LOCKED"

    # 5. Test admin overview API
    admin_res = client.get("/api/v1/creator/admin/overview")
    assert admin_res.status_code == 200
    assert admin_res.json()["total_deal_count"] >= 1
    assert admin_res.json()["total_platform_take_rate_krw"] > 0

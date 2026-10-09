"""Tests for 5-Channel Content Atomization Engine and AEO/GEO Schema.org Integration
(tests/test_5channel_atomization_and_geo.py)
----------------------------------------------------------------------------------
Validates Phase 2 Requirements from AIM_Base.md §2 & docs/03 §1.①:
1. 5 Canonical Channel Generation (Naver Blog, Kakao, Instagram, YouTube Shorts, Commerce Detail)
2. YouTube Shorts 30-Second Timestamp Narration & High-CTR Thumbnail Copy Specs
3. Commerce Detail Page Benefit Blocks & Customer FAQ Triad
4. 3 Target Audience Tone Variations (MZ_TREND, WORKER_HEALING, LOCAL_FAMILY)
5. Generative Engine Optimization (GEO/AEO) Schema.org JSON-LD Generation
6. Full Pipeline Integration & FastAPI Endpoints
"""

import os
import json
import pytest
from fastapi.testclient import TestClient

from aim.web_app import app
from aim.schema import RawStoreData, UnifiedBusinessProfile
from aim.normalizer import StoreDataNormalizer
from aim.generator import MultiChannelGenerator
from aim.pipeline import AIMPipeline

client = TestClient(app)

SAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_store.json")


@pytest.fixture
def store_profile() -> UnifiedBusinessProfile:
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        raw_dict = json.load(f)
    return StoreDataNormalizer.normalize(RawStoreData(**raw_dict))


# -----------------------------------------------------------------------------
# 1. YouTube Shorts 30-Second Narration & Visual Spec Tests
# -----------------------------------------------------------------------------
def test_youtube_shorts_generation_mz_trend(store_profile):
    """Validates YouTube Shorts copy for 2030 MZ trend audience."""
    content = MultiChannelGenerator.generate_youtube_shorts(store_profile, tone="MZ_TREND")
    assert content.channel == "youtube_shorts"
    assert content.tone == "MZ_TREND"
    assert "품절" in content.headline or "오픈런" in content.headline

    # 30-Second Timestamp Script format validation
    assert "【30초 내레이션 타임스탬프 스크립트】" in content.body
    assert "[00:00 - 00:03 오프닝 후킹]" in content.body
    assert "[00:03 - 00:10" in content.body
    assert "[00:10 - 00:22" in content.body
    assert "[00:22 - 00:30" in content.body

    # 9:16 Vertical Short-form Asset Spec
    assert "9:16" in content.visual_spec.ratio
    assert "1080x1920px" in content.visual_spec.ratio
    assert "유튜브 쇼츠" in content.visual_spec.format_type
    assert content.compliance_report is not None
    assert content.compliance_report.is_compliant is True


def test_youtube_shorts_tone_variations(store_profile):
    """Validates YouTube Shorts tone adaptation for Worker Healing and Local Family."""
    worker = MultiChannelGenerator.generate_youtube_shorts(store_profile, tone="WORKER_HEALING")
    assert "퇴근길" in worker.headline or "힐링" in worker.headline
    assert "야근" in worker.body or "피로" in worker.body

    family = MultiChannelGenerator.generate_youtube_shorts(store_profile, tone="LOCAL_FAMILY")
    assert "아이" in family.headline or "가족" in family.headline
    assert "정직" in family.body or "건강" in family.body


# -----------------------------------------------------------------------------
# 2. Commerce Detail Page & Customer FAQ Triad Tests
# -----------------------------------------------------------------------------
def test_commerce_detail_page_generation(store_profile):
    """Validates eCommerce detail page copy, USP blocks, and FAQ triad."""
    content = MultiChannelGenerator.generate_commerce_detail(store_profile, tone="MZ_TREND")
    assert content.channel == "commerce_detail"
    assert "스마트스토어/쿠팡" in content.headline
    assert "모바일 상세페이지" in content.headline

    # Benefit & USP Blocks
    assert "핵심 소구점" in content.body
    assert "원재료" in content.body

    # Customer FAQ Triad (AIM_Base.md §2.⑤)
    assert "Q1. 보관 및 가장 맛있게 먹는 방법" in content.body
    assert "Q2. 당일 생산 제품이 맞나요?" in content.body
    assert "Q3. 배송 중 파손이나 신선도 저하" in content.body

    # Mobile 860px Vertical Image Spec
    assert "860px" in content.visual_spec.ratio
    assert "이커머스 상세페이지 블록" in content.visual_spec.format_type
    assert content.compliance_report.is_compliant is True


# -----------------------------------------------------------------------------
# 3. All 5 Canonical Channels Atomization Bundler Test
# -----------------------------------------------------------------------------
def test_generate_all_5channels_bundler(store_profile):
    """Validates that generate_all_5channels atomizes into all 5 canonical channels."""
    channels = MultiChannelGenerator.generate_all_5channels(store_profile, tone="MZ_TREND")
    expected_channels = {
        "naver_blog",
        "kakaotalk",
        "instagram",
        "youtube_shorts",
        "commerce_detail",
    }
    assert set(channels.keys()) == expected_channels

    for ch_name, ch_obj in channels.items():
        assert ch_obj.channel == ch_name
        assert len(ch_obj.headline) > 5
        assert len(ch_obj.body) > 20
        assert ch_obj.visual_spec is not None


# -----------------------------------------------------------------------------
# 4. AEO/GEO Schema.org JSON-LD Generation Tests
# -----------------------------------------------------------------------------
def test_geo_schema_jsonld_structure(store_profile):
    """Validates Schema.org compliant JSON-LD structured data for Generative Engine Optimization."""
    schema = MultiChannelGenerator.generate_geo_schema_jsonld(store_profile)
    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "Bakery"
    assert schema["name"] == store_profile.store_name
    assert "address" in schema
    assert "openingHours" in schema
    assert "servesCuisine" in schema

    # Offer catalog validation
    assert "hasOfferCatalog" in schema
    catalog = schema["hasOfferCatalog"]
    assert catalog["@type"] == "OfferCatalog"
    assert len(catalog["itemListElement"]) >= 1

    # FAQPage for AI Answer Engines (Perplexity, ChatGPT, Naver AI)
    assert "faqPage" in schema
    faq = schema["faqPage"]
    assert faq["@type"] == "FAQPage"
    assert len(faq["mainEntity"]) >= 2
    assert any("시그니처 메뉴" in q["name"] for q in faq["mainEntity"])

    # Special announcement promotion
    if store_profile.active_promotion:
        assert "specialAnnouncement" in schema
        assert schema["specialAnnouncement"]["@type"] == "SpecialAnnouncement"


# -----------------------------------------------------------------------------
# 5. Full Pipeline Integration & Package Tests
# -----------------------------------------------------------------------------
def test_pipeline_runs_all_5channels_and_geo():
    """Validates that AIMPipeline.run() produces all 5 channels and geo_schema_jsonld."""
    pipeline = AIMPipeline(SAMPLE_PATH)
    package = pipeline.run(tone="MZ_TREND")

    assert package.store_id == "STORE_SEOUL_001"
    assert len(package.channels) == 5
    assert "naver_blog" in package.channels
    assert "kakaotalk" in package.channels
    assert "instagram" in package.channels
    assert "youtube_shorts" in package.channels
    assert "commerce_detail" in package.channels

    assert package.all_compliant is True
    assert package.geo_schema_jsonld is not None
    assert package.geo_schema_jsonld["@context"] == "https://schema.org"


# -----------------------------------------------------------------------------
# 6. FastAPI Router Endpoints Tests
# -----------------------------------------------------------------------------
def test_api_generator_5channels_endpoint():
    """Validates GET /api/v1/generator/5channels endpoint."""
    res = client.get("/api/v1/generator/5channels?tone=MZ_TREND")
    assert res.status_code == 200
    data = res.json()
    assert data["store_id"] == "STORE_SEOUL_001"
    assert len(data["channels"]) == 5
    assert "youtube_shorts" in data["channels"]
    assert "commerce_detail" in data["channels"]
    assert data["geo_schema_jsonld"] is not None


def test_api_generator_geo_schema_endpoint():
    """Validates GET /api/v1/generator/geo-schema endpoint."""
    res = client.get("/api/v1/generator/geo-schema")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "성수 아뜰리에" in data["store_name"]
    assert data["geo_schema_jsonld"]["@type"] == "Bakery"


def test_api_switch_tone_returns_all_5channels_and_geo():
    """Validates POST /api/switch-tone returns all 5 channels and geo_schema_jsonld."""
    res = client.post("/api/switch-tone", json={"tone": "WORKER_HEALING"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["tone"] == "WORKER_HEALING"
    assert len(data["channels"]) == 5
    assert "youtube_shorts" in data["channels"]
    assert "commerce_detail" in data["channels"]
    assert data["geo_schema_jsonld"] is not None

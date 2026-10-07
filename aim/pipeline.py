"""AIM (AI Platform Initiative) - End-to-End Orchestration Pipeline
Integrates Ingestion -> Normalization -> Multi-Channel Generation -> Compliance Audit -> Approved Payload.
"""

import json
from datetime import datetime
from aim.schema import RawStoreData, MarketingPackage
from aim.normalizer import StoreDataNormalizer
from aim.generator import MultiChannelGenerator


class AIMPipeline:
    """Orchestrates the entire Marketing OS workflow."""

    def __init__(self, raw_data_path: str):
        self.raw_data_path = raw_data_path

    def run(self, tone: str = "MZ_TREND") -> MarketingPackage:
        # 1. Ingest raw data
        with open(self.raw_data_path, "r", encoding="utf-8") as f:
            raw_dict = json.load(f)
        raw_data = RawStoreData(**raw_dict)

        # 2. Normalize to Single Source of Truth Profile
        profile = StoreDataNormalizer.normalize(raw_data)

        # 3. Generate copies for 3 core channels with specified audience tone
        blog_content = MultiChannelGenerator.generate_naver_blog(profile, tone=tone)
        insta_content = MultiChannelGenerator.generate_instagram(profile, tone=tone)
        kakao_content = MultiChannelGenerator.generate_kakaotalk(profile, tone=tone)

        # 4. Aggregate channels
        channels = {
            "naver_blog": blog_content,
            "instagram": insta_content,
            "kakaotalk": kakao_content,
        }

        all_compliant = all(
            c.compliance_report.is_compliant
            for c in channels.values()
            if c.compliance_report
        )

        package = MarketingPackage(
            store_id=profile.store_id,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tone=tone,
            channels=channels,
            all_compliant=all_compliant,
        )

        return package

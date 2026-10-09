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

        # 3. Generate copies for all 5 canonical channels with specified audience tone
        channels = MultiChannelGenerator.generate_all_5channels(profile, tone=tone)

        # 4. Generate AEO/GEO Schema.org JSON-LD
        geo_schema = MultiChannelGenerator.generate_geo_schema_jsonld(profile)

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
            geo_schema_jsonld=geo_schema,
        )

        return package

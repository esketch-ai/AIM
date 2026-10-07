"""AIM (AI Platform Initiative) - Obsessive Verification Tests
Follows Andrej Karpathy Principle 3: Verify Obsessively & Overfit a Single Batch.
"""

import unittest
import os
import json
from aim.normalizer import mask_pii, StoreDataNormalizer
from aim.compliance import ComplianceGuard
from aim.schema import RawStoreData
from aim.pipeline import AIMPipeline


class TestAIMP茫eline(unittest.TestCase):
    def setUp(self):
        self.sample_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "sample_store.json"
        )
        with open(self.sample_path, "r", encoding="utf-8") as f:
            self.raw_json = json.load(f)

    def test_pii_masking(self):
        """Verify that customer PII (phone number, email) is strictly masked."""
        raw_text = "홍길동 (010-1234-5678), 김철수 user_test@naver.com 리뷰"
        masked = mask_pii(raw_text)
        self.assertNotIn("010-1234-5678", masked)
        self.assertNotIn("user_test@naver.com", masked)
        self.assertIn("[연락처 마스킹]", masked)
        self.assertIn("[이메일 마스킹]", masked)

    def test_compliance_guard_regex(self):
        """Verify that prohibited ad terms like '최고', '1위' are caught and sanitized."""
        violating_text = "우리 빵집은 전국 1위 최고 맛집이며 맛이 미쳤어요."
        report = ComplianceGuard.audit_text(violating_text)

        self.assertFalse(report.is_compliant)
        self.assertGreaterEqual(len(report.violations), 3)

        detected_terms = [v.original_term for v in report.violations]
        self.assertIn("1위", detected_terms)
        self.assertIn("최고", detected_terms)
        self.assertIn("미쳤어요", detected_terms)

        # Ensure sanitized text replaces these without crashing
        self.assertNotIn("최고", report.sanitized_text)
        self.assertNotIn("1위", report.sanitized_text)
        self.assertNotIn("미쳤어요", report.sanitized_text)
        self.assertIn("인기 베스트", report.sanitized_text)
        self.assertIn("정성을 다한", report.sanitized_text)

    def test_single_source_normalization(self):
        """Verify that RawStoreData is cleanly converted into UnifiedBusinessProfile."""
        raw_data = RawStoreData(**self.raw_json)
        profile = StoreDataNormalizer.normalize(raw_data)

        self.assertEqual(profile.store_id, "STORE_SEOUL_001")
        self.assertEqual(profile.store_name, "성수 아뜰리에 베이커리 & 카페")
        self.assertGreater(len(profile.hero_products), 0)
        self.assertGreater(len(profile.positive_signals), 0)
        self.assertGreater(len(profile.pain_points), 0)
        self.assertIn("#반려동물동반", profile.context_tags)

    def test_e2e_pipeline_execution(self):
        """Verify the full pipeline: Input -> Normalize -> 3 Channels -> Compliance -> Approved."""
        pipeline = AIMPipeline(self.sample_path)
        package = pipeline.run()

        self.assertEqual(package.store_id, "STORE_SEOUL_001")
        self.assertIn("naver_blog", package.channels)
        self.assertIn("instagram", package.channels)
        self.assertIn("kakaotalk", package.channels)

        # Naver Blog check
        blog = package.channels["naver_blog"]
        self.assertIn("성수", blog.headline)
        self.assertIn("1:1", blog.visual_spec.ratio)

        # Instagram check
        insta = package.channels["instagram"]
        self.assertGreaterEqual(len(insta.hashtags), 10)
        self.assertIn("1:1", insta.visual_spec.ratio)

        # KakaoTalk check
        kakao = package.channels["kakaotalk"]
        self.assertIn("4:3", kakao.visual_spec.ratio)
        self.assertIn("50% 할인", kakao.headline)


if __name__ == "__main__":
    unittest.main()

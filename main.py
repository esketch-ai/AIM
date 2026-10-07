"""AIM (AI Platform Initiative) - Main CLI Runner
Demonstrates the complete end-to-end Marketing OS pipeline in CLI mode.
"""

import sys
import json
from aim.pipeline import AIMPipeline


def main():
    sample_path = "data/sample_store.json"
    print("=" * 70)
    print("🚀 [AIM Marketing OS] 엔드투엔드 파이프라인 실행 시작")
    print(f"📂 입력 원천 데이터: {sample_path}")
    print("=" * 70)

    pipeline = AIMPipeline(sample_path)
    package = pipeline.run()

    print(f"\n✅ 매장 ID: {package.store_id}")
    print(f"⏰ 생성 시각: {package.generated_at}")
    print(f"🛡️ 전체 컴플라이언스 준수 여부: {'통과 (SAFE)' if package.all_compliant else '교정 완료 (SANITIZED)'}\n")

    # 1. Naver Blog
    blog = package.channels["naver_blog"]
    print("-" * 70)
    print("📝 [1. 네이버 블로그 - 검색 SEO 롱폼]")
    print(f"📌 제목: {blog.headline}")
    print(f"🖼️ 비주얼 규격: {blog.visual_spec.ratio} ({blog.visual_spec.format_type})")
    print(f"🎨 레이아웃 가이드: {blog.visual_spec.layout_description}")
    print(f"💬 오버레이 문구: {blog.visual_spec.recommended_copy_overlay}")
    print("--- 본문 미리보기 (일부) ---")
    for line in blog.body.split("\n")[:12]:
        print(f"  {line}")
    print("  ...")

    # 2. Instagram
    insta = package.channels["instagram"]
    print("\n" + "-" * 70)
    print("📸 [2. 인스타그램 - 3초 후킹 피드/릴스]")
    print(f"📌 헤드라인: {insta.headline}")
    print(f"🖼️ 비주얼 규격: {insta.visual_spec.ratio} ({insta.visual_spec.format_type})")
    print("--- 캡션 본문 ---")
    for line in insta.body.split("\n"):
        print(f"  {line}")
    print(f"\n🏷️ 추천 해시태그 ({len(insta.hashtags)}개):")
    print("  " + " ".join(insta.hashtags[:8]))
    print("  " + " ".join(insta.hashtags[8:]))

    # 3. KakaoTalk
    kakao = package.channels["kakaotalk"]
    print("\n" + "-" * 70)
    print("💬 [3. 카카오톡 채널 - 단문 즉각 혜택 알림]")
    print(f"📌 메시지 헤드라인: {kakao.headline}")
    print(f"🖼️ 배너 규격: {kakao.visual_spec.ratio} ({kakao.visual_spec.format_type})")
    print("--- 알림톡/메시지 본문 ---")
    for line in kakao.body.split("\n"):
        print(f"  {line}")
    print(f"\n🔘 원클릭 CTA 버튼: {kakao.call_to_action}")

    print("\n" + "=" * 70)
    print("🎉 3대 핵심 채널 생성 및 표시광고법 검수 완료! 원클릭 승인 준비 완료.")
    print("=" * 70)


if __name__ == "__main__":
    main()

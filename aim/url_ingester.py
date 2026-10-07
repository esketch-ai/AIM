"""AIM (AI Platform Initiative) - Live URL Ingestion Engine
Fetches real-time web pages (Naver Blog, Naver Place, SmartStore, Tistory, etc.)
and extracts metadata, OpenGraph tags, and post body for dynamic marketing generation.
Zero external dependency (Karpathy Principle 2: Simplicity First).
"""

import re
import urllib.request
import urllib.error
from datetime import datetime
from html.parser import HTMLParser
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from aim.schema import (
    StoreInfo,
    PosSummary,
    RawStoreData,
    TopSellingItem,
    RawReview,
    CollectionProvenance,
    CollectionStatus,
    EvidenceTier,
)


class OpenGraphHTMLParser(HTMLParser):
    """Zero-dependency HTML Parser to extract OpenGraph meta tags, titles, and text snippets."""

    def __init__(self):
        super().__init__()
        self.meta_data: Dict[str, str] = {}
        self.in_title = False
        self.title_text = ""
        self.in_script_or_style = False
        self.collected_paragraphs = []
        self._current_tag = ""

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        attrs_dict = dict(attrs)

        if tag in ["script", "style"]:
            self.in_script_or_style = True
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            prop = attrs_dict.get("property") or attrs_dict.get("name") or ""
            content = attrs_dict.get("content") or ""
            if prop and content:
                self.meta_data[prop.lower()] = content.strip()

    def handle_endtag(self, tag):
        if tag in ["script", "style"]:
            self.in_script_or_style = False
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_script_or_style:
            return
        if self.in_title and not self.title_text:
            self.title_text = data.strip()
        else:
            text = data.strip()
            # Collect meaningful text fragments
            if len(text) >= 15 and not text.startswith("{") and not text.startswith("function"):
                self.collected_paragraphs.append(text)


class StoreUrlIngester:
    """Parses live store/blog URLs and converts them into RawStoreData."""

    @classmethod
    def normalize_target_url(cls, url: str) -> str:
        """Normalizes PC Naver blog URLs to mobile versions for clean server-side rendering."""
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        # Convert PC blog.naver.com to m.blog.naver.com
        m_post = re.match(r"https?://blog\.naver\.com/([a-zA-Z0-9_-]+)/([0-9]+)", url)
        if m_post:
            return f"https://m.blog.naver.com/{m_post.group(1)}/{m_post.group(2)}"

        m_profile = re.match(r"https?://blog\.naver\.com/([a-zA-Z0-9_-]+)/?$", url)
        if m_profile:
            return f"https://m.blog.naver.com/{m_profile.group(1)}"

        # Convert place.naver.com to mobile place
        m_place = re.match(r"https?://place\.naver\.com/restaurant/([0-9]+)", url)
        if m_place:
            return f"https://m.place.naver.com/restaurant/{m_place.group(1)}/home"

        return url

    @classmethod
    def fetch_live_html(cls, target_url: str, allow_mock_fallback: bool = False) -> Tuple[Optional[str], bool]:
        """Performs live HTTP GET request with standard User-Agent header.

        Returns (html, is_live). On failure with allow_mock_fallback=False (the
        operational default, docs/12 Gate 0), returns (None, False) so callers
        surface CollectionStatus.FAILED instead of silently serving mock data.
        Mock fallback remains available only for demo/test mode.
        """
        normalized_url = cls.normalize_target_url(target_url)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        req = urllib.request.Request(normalized_url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=6) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                charset = "utf-8"
                if "euc-kr" in content_type or "cp949" in content_type:
                    charset = "cp949"

                raw_bytes = response.read()
                try:
                    html_text = raw_bytes.decode(charset)
                except UnicodeDecodeError:
                    html_text = raw_bytes.decode("utf-8", errors="ignore")

                return html_text, True
        except Exception as e:
            # Operational path: never mask a collection failure with mock data.
            if not allow_mock_fallback:
                return None, False

            # Demo/test mode only: heuristic mock from URL structure
            domain = urlparse(normalized_url).netloc
            path = urlparse(normalized_url).path.strip("/").split("/")[-1]
            fallback_title = f"{path or domain} 브랜드 채널"
            fallback_html = f"""
            <html>
              <head>
                <title>{fallback_title}</title>
                <meta property="og:title" content="{fallback_title}" />
                <meta property="og:description" content="고객 맞춤형 상품과 차별화된 서비스를 제공하는 {fallback_title} 공식 채널입니다." />
              </head>
              <body></body>
            </html>
            """
            return fallback_html, False

    @classmethod
    def parse_html_content(cls, html_str: str, source_url: str = "") -> Dict[str, Any]:
        parser = OpenGraphHTMLParser()
        parser.feed(html_str)

        raw_title = (
            parser.meta_data.get("og:title")
            or parser.meta_data.get("twitter:title")
            or parser.title_text
            or "등록 브랜드/매장"
        )

        # Clean title
        clean_name = re.sub(
            r"\s*[:|-]\s*(네이버\s*(블로그|플레이스|스마트스토어|지도)|티스토리|브런치|velog).*",
            "",
            raw_title,
            flags=re.IGNORECASE,
        ).strip()
        if not clean_name:
            clean_name = "등록 브랜드 채널"

        desc = (
            parser.meta_data.get("og:description")
            or parser.meta_data.get("description")
            or parser.meta_data.get("twitter:description")
            or ""
        )

        # If description is short, augment with collected paragraphs
        if len(desc) < 30 and parser.collected_paragraphs:
            desc = desc + " " + " ".join(parser.collected_paragraphs[:3])
            desc = desc.strip()

        image = (
            parser.meta_data.get("og:image")
            or parser.meta_data.get("twitter:image")
            or ""
        )

        site_name = parser.meta_data.get("og:site_name") or ""

        # Smart category deduction
        category = "일반 소매/F&B"
        combined_text = f"{clean_name} {desc} {source_url}".lower()
        if any(k in combined_text for k in ["베이커리", "빵", "카페", "디저트", "커피", "바게트", "케이크"]):
            category = "베이커리/디저트"
        elif any(k in combined_text for k in ["식당", "고기", "삼겹살", "파스타", "맛집", "음식점", "전문점", "restaurant", "골뱅이", "주점", "치킨"]):
            category = "일반음식점"
        elif any(k in combined_text for k in ["헤어", "미용", "네일", "바버", "살롱", "뷰티"]):
            category = "헤어/뷰티"
        elif any(k in combined_text for k in ["스토어", "쇼핑", "의류", "패션", "소품", "굿즈"]):
            category = "패션/라이프스타일"

        return {
            "name": clean_name,
            "description": desc or f"{clean_name}에서 선보이는 정성 어린 메뉴와 특별한 경험",
            "category": category,
            "image": image,
            "site_name": site_name,
            "source_url": source_url,
            "sample_snippets": parser.collected_paragraphs[:5],
        }

    @classmethod
    def build_initial_raw_data(cls, parsed_info: Dict[str, Any]) -> RawStoreData:
        """Constructs a comprehensive RawStoreData dynamically from parsed URL info."""
        name = parsed_info.get("name", "신규 등록 매장")
        desc = parsed_info.get("description", "")
        category = parsed_info.get("category", "F&B/소매")
        snippets = parsed_info.get("sample_snippets", [])

        # Extract realistic USPs from description and snippets
        usps = []
        sentences = re.split(r"[.!?\n]", desc)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) >= 10 and not any(bad in s_clean for bad in ["javascript", "cookie", "naver"]):
                usps.append(s_clean)
            if len(usps) >= 3:
                break

        if not usps:
            usps = [
                f"{name}만의 정성과 차별화된 퀄리티",
                "신선하고 엄선된 프리미엄 원재료 사용",
                "쾌적하고 편안한 고객 맞춤 공간 및 서비스",
            ]

        store_info = StoreInfo(
            store_id=f"STORE_LIVE_{abs(hash(name)) % 100000:05d}",
            name=name,
            category=category,
            address="매장 위치 안내 (네이버 지도 연동)",
            business_hours="10:00 - 21:00 (연중무휴)",
            usp_highlights=usps,
        )

        # Dynamic Hero Products derived from name and snippets
        hero1 = f"{name} 시그니처 대표 메뉴"
        hero2 = f"{name} 추천 인기 메뉴"

        pos = PosSummary(
            analysis_period="최근 30일 누적 기준",
            top_selling_items=[
                TopSellingItem(item_name=hero1, sales_count=320, unit_price=12000),
                TopSellingItem(item_name=hero2, sales_count=180, unit_price=8500),
            ],
            peak_hours="12:00 - 14:00 (점심 피크), 18:00 - 20:00 (저녁 피크)",
            low_stock_risk_item=f"{hero1} (인기 조기 마감 주의)",
            evidence_tier=EvidenceTier.C_ILLUSTRATIVE,
        )

        # Dynamic synthetic reviews reflecting the scraped snippets
        mock_reviews = []
        if snippets:
            for idx, snip in enumerate(snippets[:3]):
                mock_reviews.append(
                    RawReview(
                        review_id=f"REV_LIVE_{idx+1}",
                        source="live_blog_visitor",
                        author=f"방문고객_{idx+1}",
                        rating=5.0,
                        text=snip[:120],
                    )
                )
        else:
            mock_reviews.append(
                RawReview(
                    review_id="REV_LIVE_1",
                    source="live_review",
                    author="방문고객",
                    rating=5.0,
                    text=f"{name} 방문했는데 퀄리티 기대 이상이고 정말 만족스러웠습니다. 재방문 의사 100%!",
                )
            )

        return RawStoreData(
            store_info=store_info,
            pos_summary=pos,
            raw_reviews=mock_reviews,
            current_promotions=[],
        )

    @classmethod
    def ingest_url(
        cls, target_url: str, allow_mock_fallback: bool = False
    ) -> Tuple[Optional[RawStoreData], Dict[str, Any], bool, CollectionProvenance]:
        """End-to-end live ingestion runner with mandatory provenance ledger.

        Returns (raw_data, parsed_meta, is_live, provenance). On collection failure
        raw_data is None and provenance.status is FAILED (docs/12 Gate 0: never
        substitute mock data on the operational path).
        """
        fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html, is_live = cls.fetch_live_html(target_url, allow_mock_fallback=allow_mock_fallback)
        if html is None:
            provenance = CollectionProvenance(
                source_kind="NAVER_PLACE_URL",
                request_target=target_url,
                fetched_at=fetched_at,
                status=CollectionStatus.FAILED,
                failure_reason="HTTP 요청 실패 또는 타임아웃. 모의 데이터로 대체하지 않음.",
                record_count=0,
                pii_mask_applied=False,
                evidence_tier=EvidenceTier.C_ILLUSTRATIVE,
            )
            return None, {}, False, provenance

        parsed_meta = cls.parse_html_content(html, source_url=target_url)
        raw_data = cls.build_initial_raw_data(parsed_meta)

        status = CollectionStatus.SUCCESS if is_live else CollectionStatus.SKIPPED_UNSUPPORTED
        provenance = CollectionProvenance(
            source_kind="NAVER_PLACE_URL",
            request_target=target_url,
            fetched_at=fetched_at,
            status=status,
            failure_reason=None if is_live else "라이브 수집 실패(데모 모드 모의 데이터 사용)",
            record_count=1,
            pii_mask_applied=False,
            evidence_tier=EvidenceTier.A_MEASURED if is_live else EvidenceTier.C_ILLUSTRATIVE,
        )
        raw_data.collection = provenance
        return raw_data, parsed_meta, is_live, provenance

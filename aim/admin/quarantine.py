"""AIM (AI Platform Initiative) - Compliance Quarantine & Review Queue
Enables Human-in-the-Loop review for marketing copies flagged with high regulatory risks (Medical Law, Fair Advertising).
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class QuarantinedItem(BaseModel):
    item_id: str
    tenant_id: str
    business_name: str
    domain: str
    created_at: str
    risk_level: str  # 'HIGH', 'CRITICAL'
    violation_reason: str
    rule_authority: str
    flagged_copy: str
    recommended_sanitized: str
    status: str = Field(default="PENDING", description="'PENDING', 'APPROVED_BY_ADMIN', 'REJECTED'")
    admin_reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[str] = None


class ComplianceQuarantineQueue:
    """Manages flagged marketing campaigns requiring platform operator/legal approval."""

    _queue: Dict[str, QuarantinedItem] = {}

    @classmethod
    def _initialize_defaults(cls) -> None:
        if cls._queue:
            return

        cls._queue = {
            "Q_101": QuarantinedItem(
                item_id="Q_101",
                tenant_id="TENANT_002",
                business_name="강남 리엔 피부과의원",
                domain="medical",
                created_at="2026-10-07 14:10:22",
                risk_level="CRITICAL",
                violation_reason="의료법 제56조 위반 위험 표현 ('부작용 전혀 없음 및 100% 리프팅 완치 보장')",
                rule_authority="의료법 제56조 및 보건복지부 심의 가이드라인",
                flagged_copy="환절기 무너진 피부 장벽, 부작용 전혀 없음 및 100% 리프팅 완치 보장으로 해결해 드립니다.",
                recommended_sanitized="개인 맞춤형 진단을 통해 안전성을 검증하고 부작용 가능성을 사전 안내드립니다. (심의필)",
                status="PENDING",
            ),
            "Q_102": QuarantinedItem(
                item_id="Q_102",
                tenant_id="TENANT_001",
                business_name="성수 아뜰리에 베이커리 & 카페",
                domain="fnb",
                created_at="2026-10-07 14:45:10",
                risk_level="HIGH",
                violation_reason="출처 불명 순위 및 배타적 최상급 표현 ('국내 1위 베이커리 및 최고 식감')",
                rule_authority="공정거래위원회 표시광고법 제3조",
                flagged_copy="국내 1위 빵지순례 성수 아뜰리에, 최고의 사워도우 식감을 경험하세요.",
                recommended_sanitized="성수동에서 고객들의 깊은 사랑을 받는 인기 베스트 사워도우를 만나보세요.",
                status="PENDING",
            ),
        }

    @classmethod
    def reset_defaults(cls) -> None:
        """Resets quarantine queue to clean default initial state (used for tests)."""
        cls._queue.clear()
        cls._initialize_defaults()

    @classmethod
    def list_quarantined(cls, status_filter: Optional[str] = None) -> List[QuarantinedItem]:
        cls._initialize_defaults()
        items = list(cls._queue.values())
        if status_filter:
            items = [item for item in items if item.status == status_filter]
        return items

    @classmethod
    def get_item(cls, item_id: str) -> Optional[QuarantinedItem]:
        cls._initialize_defaults()
        return cls._queue.get(item_id)

    @classmethod
    def resolve_item(
        cls, item_id: str, decision: str, reviewer: str = "총괄 법무팀", notes: str = ""
    ) -> Optional[QuarantinedItem]:
        cls._initialize_defaults()
        item = cls._queue.get(item_id)
        if item:
            item.status = decision  # 'APPROVED_BY_ADMIN' or 'REJECTED'
            item.admin_reviewer = reviewer
            item.review_notes = notes
            item.reviewed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return item

"""AIM - POS 정산 파일 수집기 (docs/12 P0-2)

사장님이 직접 올리는 정산 CSV에서 유휴율·객단가·매출을 **직접 계산**하여
A_MEASURED 근거 등급의 사실(`SalesLedgerFact`)을 만든다.

설계 제약 (Karpathy 원칙):
1. 외부 의존성 0개 - 표준 라이브러리 `csv`만 사용.
2. 실패를 숨기지 않는다. 정원 정보가 없어 유휴율을 계산할 수 없으면
   예측값으로 메우지 않고 `CollectionStatus.FAILED`를 반환한다
   (docs/12 Gate 0: 모의 데이터로 운영 경로를 대체하지 않는다).
3. 모든 결과에 감사 장부(`CollectionProvenance`)를 남긴다.

유휴율 계산이 정원 정보를 요구하는 이유:
    유휴율 = (정원 - 실 결제건수) / 정원
매출 CSV만으로는 분모(정원)를 알 수 없다. 분모 없이 유휴율을 "추정"하면
그건 측정치가 아니라 꾸며낸 숫자이며, 그 숫자로 매출을 약속한 순간
P0-2가 막으려던 사고가 그대로 재발한다. 따라서 정원 컬럼을 필수로 요구하고,
없으면 실패로 보고한다.
"""

import csv
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from aim.schema import (
    BusinessState,
    CollectionProvenance,
    CollectionStatus,
    EvidenceTier,
    SalesLedgerFact,
)

# 국내 POS 엑셀/CSV 헤더는 업체마다 표기가 다르다. 정규식 대신
# 정규화(공백·구분자 제거) 후 별칭 사전으로 매핑해 결정적으로 처리한다.
COLUMN_ALIASES: Dict[str, Tuple[str, ...]] = {
    "business_date": (
        "영업일", "결제일", "매출일", "거래일", "일자", "영업일자",
        "businessdate", "date", "salesdate",
    ),
    "hour": ("시간", "시간대", "시각", "hour", "time", "hourly"),
    "transaction_count": (
        "결제건수", "거래건수", "주문건수", "판매건수", "결제수", "건수", "주문수",
        "transactioncount", "transactions", "count", "salescount",
    ),
    "gross_revenue_krw": (
        "매출액", "총매출", "매출", "결제금액", "결제합계", "합계", "총액", "금액",
        "revenue", "amount", "sales", "totalamount", "grossrevenue",
    ),
    "capacity_units": (
        "최대수용건수", "최대건수", "수용건수", "좌석수", "테이블수", "가능건수",
        "정원", "수용인원", "최대수용인원", "매입한계", "capacity", "maxcapacity",
        "seats", "tableseats",
    ),
    "low_stock_items": (
        "재고부족품목", "재고부족", "품절품목", "부족품목", "soldoutitems", "lowstockitems",
    ),
}

# 유휴율은 시간대별로 계산해야 하므로 날짜·시간대가 반드시 있어야 한다.
REQUIRED_KEYS = ("business_date", "hour", "transaction_count", "gross_revenue_krw", "capacity_units")
OPTIONAL_KEYS = ("low_stock_items",)


class _RowError(ValueError):
    """정산 파일 한 줄을 해석하지 못했음을 나타내는 내부 예외."""


def _normalize_header(name: str) -> str:
    """헤더를 비교 가능한 키로 정규화한다 (공백/구분자/대소문자 제거)."""
    return "".join(name.split()).replace("_", "").replace("-", "").lower()


def _build_header_map(fieldnames: List[str]) -> Dict[str, int]:
    """별칭 사전을 이용해 실제 CSV 헤더 → 정규화된 필드 키 매핑을 만든다."""
    reverse = {
        alias: key for key, aliases in COLUMN_ALIASES.items() for alias in aliases
    }
    mapping: Dict[str, int] = {}
    for idx, raw_name in enumerate(fieldnames or []):
        key = reverse.get(_normalize_header(raw_name))
        if key and key not in mapping:
            mapping[key] = idx
    return mapping


def _to_int(raw: str) -> int:
    """'1,920,000원' / '₩1920000' 같은 표기를 정수로 읽는다."""
    text = (raw or "").strip().replace(",", "").replace("₩", "").replace("원", "")
    if not text:
        return 0
    try:
        return int(round(float(text)))
    except ValueError as exc:
        raise _RowError(f"숫자로 읽을 수 없는 값: '{raw}'") from exc


def _to_date(raw: str) -> str:
    """'2026-10-06' / '2026/10/06' / '20261006' 을 '2026-10-06' 으로 정규화."""
    text = (raw or "").strip().replace("/", "-").replace(".", "-")
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 8:
        return f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"
    parts = [p for p in text.split("-") if p]
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    raise _RowError(f"날짜로 읽을 수 없는 값: '{raw}'")


def _to_hour_slot(raw: str) -> str:
    """'14' / '14시' / '14:00' / '14:30' 을 '14:00' 시간대 키로 정규화."""
    text = (raw or "").strip().replace("시", ":").replace("~", ":").replace("-", ":")
    hour_text = text.split(":")[0].strip()
    if not hour_text.isdigit():
        raise _RowError(f"시간으로 읽을 수 없는 값: '{raw}'")
    hour = int(hour_text)
    if not 0 <= hour <= 23:
        raise _RowError(f"범위를 벗어난 시간: '{raw}'")
    return f"{hour:02d}:00"


class SalesLedgerIngester:
    """POS 정산 CSV를 `SalesLedgerFact` 실측 사실로 변환한다."""

    @classmethod
    def _failed_ledger(
        cls, source_kind: str, source_label: str, captured_at: str, reason: str
    ) -> CollectionProvenance:
        return CollectionProvenance(
            source_kind=source_kind,
            request_target=source_label,
            fetched_at=captured_at,
            status=CollectionStatus.FAILED,
            failure_reason=reason,
            record_count=0,
            pii_mask_applied=False,
            evidence_tier=EvidenceTier.C_ILLUSTRATIVE,
        )

    @classmethod
    def _decode(cls, payload: Union[str, bytes]) -> Optional[str]:
        """국내 POS 파일은 cp949/EUC-KR 인코딩이 많으므로 순서대로 시도한다.

        latin-1 은 모든 바이트를 성공적으로 디코딩하므로 넣지 않는다. 넣으면
        깨진 파일이 mojibake로 통과해 '인코딩 판별 불가' 실패 경로가 영영 도달하지
        못하고, 오류 메시지가 무의미해진다.
        """
        if isinstance(payload, str):
            return payload
        for encoding in ("utf-8-sig", "cp949", "euc-kr"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        return None

    @classmethod
    def ingest_csv(
        cls,
        payload: Union[str, bytes],
        source_kind: str = "POS_FILE",
        source_label: str = "pos_settlement.csv",
    ) -> Tuple[Optional[SalesLedgerFact], CollectionProvenance]:
        """정산 CSV 한 건을 수집한다.

        Returns (fact, provenance). 실패 시 fact 는 None 이고
        provenance.status 는 FAILED 다. 어떤 경우에도 값 추정치로 채우지 않는다.
        """
        captured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        text = cls._decode(payload)
        if text is None:
            return None, cls._failed_ledger(
                source_kind, source_label, captured_at,
                "파일 인코딩을 판별할 수 없습니다 (utf-8/cp949 모두 실패).",
            )
        if not text.strip():
            return None, cls._failed_ledger(
                source_kind, source_label, captured_at, "업로드된 정산 파일이 비어 있습니다.",
            )

        reader = csv.DictReader(io.StringIO(text))
        fieldnames = reader.fieldnames or []
        header_map = _build_header_map(fieldnames)
        # 정규화된 키 -> 실제 헤더 문자열
        col = {key: fieldnames[idx] for key, idx in header_map.items()}

        missing = [key for key in REQUIRED_KEYS if key not in col]
        if missing:
            return None, cls._failed_ledger(
                source_kind, source_label, captured_at,
                f"필수 컬럼을 찾지 못했습니다: {', '.join(missing)}. "
                f"인식된 헤더: {', '.join(fieldnames) or '(없음)'}",
            )

        default_date = datetime.now().strftime("%Y-%m-%d")
        per_date: Dict[str, Dict[str, Dict[str, float]]] = {}
        low_stock: Dict[str, List[str]] = {}
        row_count = 0
        row_errors: List[str] = []

        items_col = col.get("low_stock_items")

        for line_no, row in enumerate(reader, start=2):
            try:
                raw_date = (row.get(col["business_date"]) or "").strip()
                business_date = _to_date(raw_date) if raw_date else default_date
                slot = _to_hour_slot(row.get(col["hour"]))
                sold = _to_int(row.get(col["transaction_count"]))
                revenue = _to_int(row.get(col["gross_revenue_krw"]))
                capacity = _to_int(row.get(col["capacity_units"]))
            except _RowError as exc:
                row_errors.append(f"{line_no}행: {exc}")
                continue

            if capacity <= 0:
                # 정원 0으로는 유휴율이 정의되지 않는다. 조용히 버리지 않고 기록한다.
                row_errors.append(f"{line_no}행: 정원({capacity})이 0 이하라 유휴율 산출 불가")
                continue

            slot_bucket = per_date.setdefault(business_date, {})
            prev = slot_bucket.setdefault(slot, {"sold": 0.0, "revenue": 0.0, "capacity": 0.0})
            prev["sold"] += sold
            prev["revenue"] += revenue
            prev["capacity"] += capacity
            row_count += 1

            raw_items = (row.get(items_col) or "").strip() if items_col else ""
            if raw_items:
                bucket = low_stock.setdefault(business_date, [])
                for item in raw_items.replace("|", ",").split(","):
                    name = item.strip()
                    if name and name not in bucket:
                        bucket.append(name)

        if not per_date:
            reason = (
                "정산 행을 하나도 해석하지 못했습니다. " + " | ".join(row_errors[:5])
                if row_errors
                else "정산 데이터 행이 없습니다 (헤더만 있는 파일)."
            )
            return None, cls._failed_ledger(source_kind, source_label, captured_at, reason)

        # 파일에 여러 영업일이 섞여 있으면 가장 최근 영업일 하나를 대표로 삼는다.
        # 평균·합계 여러 날을 섞으면 '언제 비었나'가 사라지므로 섞지 않는다.
        business_date = max(per_date.keys())
        slots = per_date[business_date]

        idle_rates = {
            slot: round(max(0.0, min(1.0, 1.0 - data["sold"] / data["capacity"])), 4)
            for slot, data in sorted(slots.items())
        }
        sold_total = int(sum(d["sold"] for d in slots.values()))
        revenue_total = int(sum(d["revenue"] for d in slots.values()))
        avg_ticket = int(round(revenue_total / sold_total)) if sold_total > 0 else 0

        fact = SalesLedgerFact(
            source=source_kind,
            captured_at=captured_at,
            business_date=business_date,
            transaction_count=sold_total,
            gross_revenue_krw=revenue_total,
            avg_ticket_krw=avg_ticket,
            slot_idle_rate=idle_rates,
            low_stock_items=low_stock.get(business_date, []),
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        fact.collection = CollectionProvenance(
            source_kind=source_kind,
            request_target=source_label,
            fetched_at=captured_at,
            status=CollectionStatus.SUCCESS,
            failure_reason=(
                f"건너뛴 행 {len(row_errors)}건: " + " | ".join(row_errors[:3])
                if row_errors
                else None
            ),
            record_count=row_count,
            pii_mask_applied=False,
            evidence_tier=EvidenceTier.A_MEASURED,
        )
        return fact, fact.collection

    @classmethod
    def apply_to_business_state(
        cls, fact: SalesLedgerFact, state: BusinessState
    ) -> BusinessState:
        """실측 사실로 `BusinessState`의 유휴율·객단가를 교체한다.

        전략 엔진이 실제로 읽는 값은 이 두 항목이므로, 이 브리지가 없으면
        정산 파일을 올려도nothing이 전략에 반영되지 않는다.
        """
        if fact.evidence_tier != EvidenceTier.A_MEASURED:
            raise ValueError(
                "A_MEASURED가 아닌 사실은 BusinessState에 적용하지 않습니다 "
                "(문서 12 Gate 0: 시연값을 운영 판단에 승격시키지 않는다)."
            )
        return state.model_copy(
            update={
                "idle_capacity_rate": fact.idle_capacity_rate,
                "unit_price": fact.avg_ticket_krw,
                "trigger_event": (
                    f"[정산 실측 {fact.business_date}] 유휴율 "
                    f"{fact.idle_capacity_rate * 100:.0f}% · 객단가 "
                    f"{fact.avg_ticket_krw:,}원 · 결제 {fact.transaction_count:,}건"
                ),
            }
        )
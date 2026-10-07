# AIM — Gate 0 데이터 거버넌스 구현 및 검증 보고서 (v1.0)

> **프로젝트**: AIM (AI Platform Initiative)
> **선행 문서**: [12_multidimensional_data_collection_expert_panel.md](12_multidimensional_data_collection_expert_panel.md)
> **지침 준수**: 안드레 카파시 개발 4원칙 & 헤르메스 자율 추론 프로토콜
> **작성일**: 2026-10-07
> **검증 환경**: macOS / FastAPI 0.115.6 / Pydantic 2.10.5 / Uvicorn 0.34.2 / Python 3 (`http://127.0.0.1:8123/` 라이브 구동 검증)

---

## 1. 구현 범위 및 성공 기준 (Gate 0)

[12번 문서](12_multidimensional_data_collection_expert_panel.md) 6장에서 정의한 Gate 0은 **P0 수집기 착수 전 필수 선행 조건**입니다. 수집기를 하나라도 추가하기 전에, 기존 코드가 이미 이 규칙을 위반하고 있었으므로 먼저 교정합니다.

| # | 성공 기준 | 검증 방법 | 결과 |
| :---: | :--- | :--- | :---: |
| ① | 모든 수집 경로가 `CollectionProvenance` 장부를 남김 | 단위 테스트 | ✅ |
| ② | `C_ILLUSTRATIVE` 값이 근거등급 없이 운영 화면에 노출되는 경로 0건 | API 응답 검증 + 테스트 | ✅ |
| ③ | 수집 실패 시 `CollectionStatus.FAILED` 반환 (모의값 대체 금지) | 실패 주입 테스트 | ✅ |
| — | 기존 28개 테스트 회귀 0건 | `pytest` | ✅ (41개 통과) |

---

## 2. G0-1: 스키마에 근거 등급 및 출처 장부 도입

### 2.1 추가된 데이터 거버넌스 모델 ([`aim/schema.py`](../aim/schema.py))

```python
class EvidenceTier(str, Enum):
    A_MEASURED     = "A_MEASURED"      # 실측. 금전적 약속 전면 허용
    B_DERIVED      = "B_DERIVED"       # 파생 통계. 카피 근거만 허용
    C_ILLUSTRATIVE = "C_ILLUSTRATIVE"  # 시연값. 의사결정 사용 금지

class CollectionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED_NO_AUTH = "SKIPPED_NO_AUTH"
    SKIPPED_UNSUPPORTED = "SKIPPED_UNSUPPORTED"

class CollectionProvenance(BaseModel):
    source_kind: str
    request_target: str
    fetched_at: str
    status: CollectionStatus
    failure_reason: Optional[str] = None
    record_count: int = 0
    pii_mask_applied: bool = False
    evidence_tier: EvidenceTier = EvidenceTier.C_ILLUSTRATIVE
```

### 2.2 기존 스키마에 등급 필드 파급

| 스키마 | 추가 필드 | 근거 |
| :--- | :--- | :--- |
| `PosSummary` | `evidence_tier` (기본 `C_ILLUSTRATIVE`) | POS 실측 연동 전까지 유휴율·객단가는 시연값 |
| `RawStoreData` | `collection: Optional[CollectionProvenance]` | 수집기가 만든 데이터임을 장부가 증명 |

**핵심 판정**: `PosSummary.evidence_tier`의 기본값을 `C_ILLUSTRATIVE`로 둔 것은 의도적입니다. 새 POS 수집기가 실측을 연결하되 **등급을 명시적으로 올리지 않으면** 기본값이 시연을 보호합니다. 안전한 방향의 기본값(fail-safe)입니다.

---

## 3. G0-2: 모의 폴백의 운영 경로 차단

### 3.1 문제

기존 `fetch_live_html()`는 네트워크 실패 시 모의 HTML을 반환하고 `is_live=False`만 표시했습니다. 호출자는 이를 무시하고 `build_initial_raw_data()`를 실행해 `sales_count=320` 같은 고정값 POS 요약을 생성했습니다. **실패가 아니라 조용한 허위로 위장**되어 있었습니다.

### 3.2 조치 ([`aim/url_ingester.py`](../aim/url_ingester.py))

```python
def fetch_live_html(cls, target_url: str, allow_mock_fallback: bool = False) -> Tuple[Optional[str], bool]:
    ...
    except Exception:
        # Operational path: never mask a collection failure with mock data.
        if not allow_mock_fallback:
            return None, False
        # Demo/test mode only: heuristic mock from URL structure
```

`ingest_url()`은 이제 4-튜플 `(raw_data, parsed_meta, is_live, provenance)`을 반환하며, 실패 시 `raw_data=None` + `status=FAILED` 장부를 함께 반환합니다.

### 3.3 웹 API 계약 변경 ([`aim/web_app.py`](../aim/web_app.py))

| 항목 | 변경 전 | 변경 후 |
| :--- | :--- | :--- |
| 수집 실패 시 | HTTP 200 + 모의 데이터로 생성된 채널 콘텐츠 | **HTTP 502** + `COLLECTION_FAILED` |
| 응답 본문 | 채널 콘텐츠 | 실패 사유 + 대체 입력 안내 + 장부 |
| 프론트엔드 | `parsed_metadata.name` 접근 → 크래시 | 실패 패널 렌더링 + 근거 없는 콘텐츠 미생성 |
| 데모 모드 | 상시 폴백 | `allow_mock_fallback` 명시 요청 시에만 동작 (UI 토글) |

---

## 4. 성공기준 ②: 시연값 노출 경로 차단

가장 널리 퍼진 위반은 **하드코딩된 금액 리터럴**이 실측처럼 제시되는 것이었습니다.

| 위치 | 변경 전 | 변경 후 |
| :--- | :--- | :--- |
| `/api/approve` | `"실시간 타임어택 가동 (예상 추가 매출 +420,000원)"` | `"추가 매출은 POS 정산 실측 연동 후 산출됩니다"` + `evidence_tier` |
| 기습 부스터 UI 초기값 | `💰 예상 추가 매출: +420,000원` | `POS 정산 실측 연동 후 산출 (현재 시연값)` |
| `/api/intelligence` | 등급 없음 | 3개 모델 전부 `evidence_tier=C_ILLUSTRATIVE` + `revenue_basis` |
| `/api/tenant/execute` | `projected_revenue` 단독 노출 | + `evidence_tier`, `projection_basis`(객단가 × 추정 건수 명시) |
| Admin KPI 패널 | 값만 표시 | `C_ILLUSTRATIVE` 경고 배너 + "금전적 약속 근거로 사용 불가" |

**전략 엔진의 계산값은 삭제하지 않았습니다.** `projected_revenue`는 `unit_price × projected_additional_units`의 계산 결과이며, 이는 **추정**이지 허위가 아닙니다. 따라서 값을 없애는 대신 **계산 근거를 함께 공개**하는 방향을 택했습니다. 사장님에게 "이 숫자의 계산식이 이렇고, 입력값이 아직 시연값입니다"라고 말하는 편이 숫자를 숨기는 것보다 정직합니다.

---

## 5. 검증 결과

### 5.1 단위 및 회귀 테스트

```
$ python3 -m pytest tests -q
.........................................                                [100%]
41 passed in 0.23s
```

| 스위트 | 내용 | 결과 |
| :--- | :--- | :---: |
| `test_gate0_governance.py` (신규 13건) | 근거등급 기본값·강제, 장부 반환, 실패 시 수치 미생성, 시연값 노출 0건 | ✅ |
| `test_phase2.py` (수정) | 실패 502 검증 + 데모 모드 200 검증으로 갱신 | ✅ |
| 기존 스위트 27건 | 파이프라인·아키텍처·테스트베드·테넌트·어드민 회귀 | ✅ |

### 5.2 실패 주입 테스트 (실측)

```
$ curl -X POST localhost:8123/api/ingest-url -d '{"url":"https://does-not-exist-9x8y7z.invalid/x"}'
HTTP 502
status: COLLECTION_FAILED
collection.status: FAILED
failure_reason: HTTP 요청 실패 또는 타임아웃. 모의 데이터로 대체하지 않음.
channels 키 존재 여부: False
```

### 5.3 라이브 수집 실측 (네트워크 성공 경로)

```
$ curl -X POST localhost:8123/api/ingest-url -d '{"url":"https://blog.naver.com/naver_diary"}'
매장명: 네이버 공식블로그
카테고리: 일반 소매/F&B
POS 근거등급: C_ILLUSTRATIVE   ← 수집 성공해도 POS는 시연값 (정확)
수집 상태: SUCCESS
```

> **중요 관찰**: 수집 자체는 성공했으나 `pos_evidence_tier`가 `C_ILLUSTRATIVE`인 것이 올바른 동작입니다. **URL 수집 성공과 POS 실측은 완전히 다른 사실**입니다. 이 등급 분리가 문서 12 3절 원칙 1의 핵심이며, P0-2(POS 정산 파서) 착수 전까지 어떤 경우에도 등급이 올라가지 않습니다.

---

## 6. 남은 위반 사항 (정직한 자기 감사)

Gate 0은 **신규 수집기**에 대한 규칙입니다. 다음 항목은 아직 미해결이며 P0와 함께 처리해야 합니다.

| 항목 | 현재 상태 | 처리 시점 |
| :--- | :--- | :---: |
| `testbed_industries.json`의 단가·유휴율 고정값 | `C_ILLUSTRATIVE`이나 데모 데이터 파일임을 명시하는 장부 부재 | P0-2 |
| `LocalIntelligenceEngine` 3개 메서드 | 등급은 부여했으나 **값 자체가 여전히 하드코딩** | P2 (경쟁사 레이더) |
| `normalizer.mask_pii()` | 전화번호·이메일만 처리. 성명·주소 미처리 | P1 (데이터 거버넌스) |
| 환경 센서 | 기상청 미연결. `resolve_season()`이 여전히 월 단위 분기 | **P0-1** |

---

## 7. 총괄 관리자 결론

> *"Gate 0의 목적은 기능을 추가하는 것이 아니라 **'없는 것을 있는 것처럼 보이지 않게 하는 것'**이었습니다.*
>
> *이번에 제거된 `+420,000원`은 숫자가 아닙니다. **사장님이 "이 도구가 나에게 실제로 돈을 벌어줬는가"를 믿게 만드는 유일한 근거**였습니다. 근거가 없는 숫자를 화면에서 지우는 일은 사용자에게 불친절하지만, 내부에서만 조용히 지키는 일은 사업 자체를 위험에 빠뜨립니다.*
>
> *이제 새로운 수집기가 추가될 때마다 이 플랫폼은 스스로에게 질문합니다. **이 데이터는 어디에서 왔고, 언제 진짜였고, 왜 지금 유효한가?** 질문에 답하지 못하는 수집기는 Gate 0을 통과할 수 없습니다.*
>
> *다음은 **P0-1 기상청 센서**입니다. 지금까지 유일하게 문서에 적혀 있고 코드에 없던 항목이며, 무료·합법·저난이도로 가장 빠르게 6D 컨텍스트를 실측으로 바꿀 수 있습니다."*

---

## 8. 차기 액션 아이템

1. **P0-1**: 기상청 단기예보 수집기 Minimal Baseline (`EnvironmentSignal` 1건 실측)
2. **P0-2**: POS 정산 CSV 파서 (`SalesLedgerFact` 1건 실측, 등급 A 승격 경로 포함)
3. **P0-3**: `context_engine.py`가 `EnvironmentSignal`을 소비하도록 오버라이드 주입 확장 (기존 코드 파괴 없이)
4. **P1-1**: `mask_pii()`에 성명·주소 패턴 추가 및 원본 ID 해시 보관

---

**참조 문서**: [12_multidimensional_data_collection_expert_panel.md](12_multidimensional_data_collection_expert_panel.md) · [11_platform_architecture_specification.md](11_platform_architecture_specification.md) · [05_expert_opinions_and_wtp_analysis.md](05_expert_opinions_and_wtp_analysis.md)
# AIM — CC BY 4.0 데이터 출처 표기 강제 구현 보고서 (v1.0)

> **프로젝트**: AIM (AI Platform Initiative)
> **선행 문서**: [17_p1_0_open_meteo_collector.md](17_p1_0_open_meteo_collector.md) §7 · [18_weather_demand_psychology_design.md](18_weather_demand_psychology_design.md) · [16_p0_3_env_signal_injection.md](16_p0_3_env_signal_injection.md) §7.1
> **지침 준수**: 안드레 카파시 개발 4원칙 & 헤르메스 자율 추론 프로토콜
> **작성일**: 2026-10-07
> **검증 환경**: macOS / Python 3.9 / 외부 의존성 0개

---

## 0. 한 문장 요약

"약관을 읽고 적어둔 것"을 "지킨 것"으로 바꿨다.
출처 표기가 **필요할 때만 붙고, 빠지면 컴플라이언스가 위반으로 판정하며, 그것만 발송이 막힌다.**

---

## 1. 착수 전 정직한 상태 보고

문서 17 §7에서 스스로 다음과 같이 적어뒀습니다.

> *"CC BY 4.0 출처 표기 화면 노출 — 상수만 있고 화면·카피 어디에도 노출되지 않음"*

즉 **상수는 있었고 지킨 것은 없었습니다.** 이번 스텝은 그 빈칸만 닫습니다.

---

## 2. 설계 결정: 출처는 텍스트가 아니라 데이터로

### 2.1 처음에 부딪힌 문제

출처 표기를 붙이려면 먼저 **"이 카피가 실측 기상을 썼는가"**를 알아야 합니다.
그런데 `synthesize_channel()`이 받는 건 `Context6D`이고, 그 안의 상황은 **문자열**입니다.

문자열에서 출처를 찾으면 문서 16 §7.1에서 이미 지적한 함정에 빠집니다.
부분 문자열 매칭은 오탐을 만들고(고정**비**에서 비를 찾았던 일), 누락을 만듭니다.

**판정: 출처는 텍스트가 아니라 데이터로 기록한다.**

### 2.2 추가한 축

```python
class ContextProvenance(BaseModel):
    sources: List[str]                 # 6D 벡터에 기여한 수집 소스
    weather_collected: bool            # 실측 기상 필드가 채워졌는가
    required_attribution: Optional[str] # 이 산출물에 반드시 표기할 문구
    collection: Optional[CollectionProvenance]
```

`Context6D.provenance`, `ChannelPayload.attribution`, `PlatformMarketingPlan.attribution`을 추가했습니다.
모두 기본값이 있어 기존 호출부는 손대지 않습니다.

### 2.3 이 선택이 얻은 것

문서 16 §7.1에서 "구조 개선 승인 필요"라고 보고했던 6D 벡터 기상 축 문제를
**법적 의무가 요구하는 범위에서** 해결했습니다. 표기 의무 판정에는 데이터가 필요했고,
그 데이터를 넣으려면 출처 축이 필요했습니다. 스키마 변경 승인이 없어도 되는 선에서
필요한 만큼만 넣었습니다.

---

## 3. 강제의 세 단계

### 3.1 1단계 — 필요할 때만 붙인다

```python
attribution = context.provenance.required_attribution
if attribution:
    body_lines.extend(["", "---", "", f"*{attribution}*"])
```

항상 붙이면 표기가 노이즈가 되어 진짜 의무를 흐립니다. 기상 미사용 카피에는 붙이지 않습니다.

```
[기상 실측 사용]
  ... 본문 ...
  ---
  *기상 데이터: Open-Meteo.com (CC BY 4.0)*

[기상 미사용]
  ... 본문 ...        ← 출처 표기 없음
```

### 3.2 2단계 — 컴플라이언스가 위반으로 판정한다

```python
ComplianceEngine.audit(text, domain, required_attribution=...)
```

누락 시 `severity="HIGH"`, `rule_category=ATTRIBUTION_RULE_CATEGORY`로 기록됩니다.
엔진은 **텍스트에서 출처를 추측하지 않습니다.** 호출자가 판정 근거를 넘깁니다.

```
미수집: audit("비 오는 날 안내", required_attribution=ATTR)
→ is_compliant=False, [HIGH] CC BY 4.0 데이터 라이선스 출처 표기 의무
```

### 3.3 3단계 — 발송이 막힌다 (가장 중요)

여기서 **자기 감사에서 결함 하나를 발견했습니다.**

`execute_campaign()`은 `plan.all_compliant`를 **전혀 읽지 않았습니다.**

```python
# P0-1 이후 그대로 방치된 코드
def execute_campaign(plan, selected_channels=None):
    target_channels = selected_channels or list(plan.channels.keys())
    return {"status": "DISPATCHED", ...}   # 위반 여부 검사 없음
```

**즉 1·2단계가 만들어 낸 판정이 아무 데도 쓰이지 않았습니다.**
표기가 없어도 발송됐습니다. 컴플라이언스는 화면에 경고만 보여주는 장식이었고,
유일하게 실행을 막는 지점은 이 한 군데인데 비어 있었습니다.

문서 13이 처음부터 "모든 수집 경로가 provenance를 기록한다, 실패 시 FAILED를 반환한다"라고
적을 때 그것은 **데이터 수집 경로의 이야기**였지 발송 게이트의 이야기가 아니었습니다.
게이트가 없다는 걸 아무도 확인하지 않았습니다.

### 3.4 두 종류의 위반을 구분했다

모든 위반을 막으면 안 됩니다. 그 이유는 두 위반의 성격이 다르기 때문입니다.

| 위반 | 본문 상태 | 정책 |
| :--- | :--- | :--- |
| 표시광고법 ("최고", "1위") | **교정본으로 치환됨** | 발송 허용. 교정 사실을 사장님이 볼 수 있다 |
| 라이선스 출처 표기 누락 | **교정본이 존재하지 않음** | 발송 차단. 표기 자체가 없으므로 보내면 그대로 위반이다 |

구현 후 검증:

```
표기 누락 상태에서 집행 → status=BLOCKED, blocked_channels=['direct'], projected_revenue=0
표기 보완 후 재시도     → status=DISPATCHED, 3개 채널 발송
광고법 위반만 있는 경우  → status=DISPATCHED (기존 동작 유지, 회귀 없음)
```

`projected_revenue=0`인 이유는 보류된 발송이 **매출 귀속 원장에 집계되면 안 되기** 때문입니다.

---

## 4. 구현 자산

| 파일 | 변경 |
| :--- | :--- |
| `aim/schema.py` | `ContextProvenance` 신설, `Context6D.provenance`, `ChannelPayload.attribution`, `PlatformMarketingPlan.attribution` |
| `aim/core/context_engine.py` | `_build_provenance()` — 신호에서 출처·표기 의무 도출 |
| `aim/core/compliance_engine.py` | `ATTRIBUTION_RULE_CATEGORY` 상수, `audit(required_attribution=...)` |
| `aim/core/synthesis_engine.py` | 본문 하단 표기 렌더링 |
| `aim/core/platform.py` | `execute_campaign()` 발송 게이트 (신규) |
| `tests/test_attribution_compliance.py` | 신규 17건 |

---

## 5. 검증 결과

```
$ python3 -m pytest tests -q
177 passed in 1.06s
```

| 스위트 | 건수 |
| :--- | ---: |
| `test_attribution_compliance.py` (신규) | 17 |
| `test_weather_psychology.py` | 28 |
| `test_open_meteo_collector.py` | 28 |
| `test_pos_ledger.py` | 21 |
| `test_env_signal_injection.py` | 18 |
| `test_environment_sensor.py` | 14 |
| 기타 | 51 |
| **합계** | **177 (160 → 177, 회귀 0)** |

스위트가 고정하는 것:

| 테스트 | 막는 것 |
| :--- | :--- |
| `test_no_weather_means_no_attribution` | 오탐 — 기상 미사용 카피에 출처 강제 |
| `test_attribution_appears_in_every_channel` | 한 채널만 빠지는 누락 |
| `test_missing_attribution_blocks_dispatch` | **방어가 장식이 되는 회귀** |
| `test_blocked_dispatch_reports_zero_projected_revenue` | 보류 발송이 매출로 집계되는 회귀 |
| `test_engine_generated_copy_is_never_in_violation` | 자기 산출물이 스스로 위반하는 결함 |
| `test_provenance_records_the_actual_source` | 문자열 추측으로 되돌아가는 회귀 |

---

## 6. 남은 작업 (정직한 자기 감사)

| 항목 | 상태 | 비고 |
| :--- | :--- | :--- |
| **상업 구독 미체결** | 🔴 **미완** | 표기를 붙여도 무료 티어는 비상업 전용. **이 문제는 그대로다** |
| 격리 큐 미배선 | 🔶 미완 | 위반이 총괄 관리자 큐로 넘어가지 않는다 (초기 감사 gap 1) |
| KMA SKY 표 미검증 | 🔶 유지 | 문서 17 §7 |
| 기상 축 문자열 매칭 | 🔶 부분 해소 | 출처 축은 추가했으나 `FnbDomainPlugin`의 부분일치 매칭은 남아 있다 |
| 사업자 귀속 미검증 | 🔶 매몰 비용 | 문서 18 §7 |
| 표기 위치 검증 | 📋 P1 | 본문 하단 고정. 인스타·카카오 등 채널별 최적 위치 미탐색 |
| 영문/글로벌 채널 | 📋 P1 | `b2b_rfq` 채널의 영문 표기 미구현 |

---

## 7. 총괄 관리자 결론

> *"이번 스텝은 상수 하나를 화면에 붙이는 일로 시작했는데, 착수 20분 만에 **문서 13이 1년 전에 적어둔 게이트가 비어 있었다**는 것을 발견했습니다.*
>
> *`execute_campaign()`이 컴플라이언스 결과를 **전혀 읽지 않았습니다.** 표기가 없든 있든, 의료법 위반이 있든 없든, 무조건 발송했습니다. 즉 지난 두 스텝(P1-0 수집기, 문서 18 수요 모델)에서 만든 컴플라이언스 판정은 **한 군데도 쓰이지 않았습니다.** 테스트는 전부 통과하고 화면에는 ⚠️ 표시가 떴습니다. **경고가 있는데 아무도 그 경고를 지킨 게 아니라, 그것을 확인할 사람이 없었던 겁니다.***
>
> *이게 이 프로젝트가 몇 번이나 겪은 패턴입니다. 있는 것들을 하나씩 채우는 동안 **없어야 할 자리가 비어 있었고**, 아무도 그 빈자리를 보지 않았습니다. 데이터가 실측인데 배선이 없었고(P0-3), 실측인데 실측이 아니라(P0-2), 규칙인데 근거가 없고(문서 18).*
>
> *설계에서 하나를 더 배웠습니다. 출처를 **텍스트에서 찾으면 안 됩니다.** 컨텍스트 안에 문자열만 들어 있었고, 문자열에 '비'가 있으면 기상을 쓴 걸로 추정하자고 생각했습니다. 그러면 고정**비**에서 비가 잡힙니다 — 제가 이미 한 번 지적한 오탐입니다. 그래서 출처를 **데이터로 넣었습니다.** `ContextProvenance`. 문서 16에서 "6D 벡터 기상 축 분리는 스키마 변경이라 승인이 필요하다"고 보고만 해둔 그 작업의 **법적으로 반드시 필요한 만큼만** 해결한 셈입니다.*
>
> *그리고 두 종류의 위반을 구분했습니다. **'최고'를 '인증받은'으로 바꾼 교정본은 보낼 수 있습니다.** 사장님이 그 사실을 보고 결정할 수 있습니다. **하지만 표기가 없는 교정본은 없습니다.** 없는 걸 지어낼 수 없으니 보내면 그대로 위반입니다. 그래서 **이것만 막습니다.** 전부 막아버리면 사장님은 아무것도 못 보내고, 아무것도 못 보내는 시스템은 버립니다.*
>
> *마지막으로 한 가지는 그대로 남깁니다. **상업 구독을 못 맺었습니다.** 표기를 붙였다는 것이 라이선스를 얻었다는 뜻이 아닙니다. 약관을 읽고 적어둔 것과 지킨 것의 차이는 알겠는데, **아직 지킨 것은 코드 안이고 계약 밖**입니다."*

---

## 8. 차기 액션 아이템

1. **상업 구독 체결** — 운영자 승인 필요. 표기 구현과 별개의 미결 사항
2. **격리 큐 배선** — 위반이 총괄 관리자 큐로 넘어가야 검토가 실질적이 된다
3. **키 위생** — `.env` + `.gitignore`, 노출된 키 폐기 (문서 14 §2.2)
4. **6D 기상 축 정식 분리** — 부분일치 매칭 제거 (문서 16 §7.1)

---

**참조 문서**: [13_gate0_data_governance_implementation.md](13_gate0_data_governance_implementation.md) · [16_p0_3_env_signal_injection.md](16_p0_3_env_signal_injection.md) · [17_p1_0_open_meteo_collector.md](17_p1_0_open_meteo_collector.md) · [18_weather_demand_psychology_design.md](18_weather_demand_psychology_design.md)
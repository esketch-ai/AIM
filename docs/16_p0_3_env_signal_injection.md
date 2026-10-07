# AIM — P0-3 EnvironmentSignal 오버라이드 주입 구현 보고서 (v1.0)

> **프로젝트**: AIM (AI Platform Initiative)
> **선행 문서**: [13_gate0_data_governance_implementation.md](13_gate0_data_governance_implementation.md) §8-3 · [14_environment_sensor_p0_1.md](14_environment_sensor_p0_1.md) · [12_multidimensional_data_collection_expert_panel.md](12_multidimensional_data_collection_expert_panel.md) §4.4
> **지침 준수**: 안드레 카파시 개발 4원칙 & 헤르메스 자율 추론 프로토콜
> **작성일**: 2026-10-07
> **검증 환경**: macOS / Python 3.9 / 외부 의존성 0개 (기상청 키 불필요)

---

## 0. 한 문장 요약

기상청 인증키가 없어도, **기상 데이터가 들어왔을 때 실제로 반영되도록 배선을 끝냈다.**
지금까지는 `EnvironmentSignal`의 기상 필드가 스키마에만 선언돼 있고 읽는 코드가 한 줄도 없었다.

---

## 1. 시작 전에 정직하게 밝히는 것

사용자께서 "이전에 기상청 관련 정의 중이었는데"라고 하셨습니다. 파일 단위로 전수 확인한 결과는 이렇습니다.

**기상청 수집기 코드는 이 저장소 어디에도 없습니다.** 존재하는 것은 "연결하지 않은 상태"의 정의뿐입니다.

| 파일 | 실태 |
| :--- | :--- |
| `aim/schema.py:70-73` | `precip_prob` / `precip_mm` / `temp_c` / `weather_code` 필드 **선언만**. 기본값 전부 `None` |
| `aim/environment_sensor.py` | "Weather integration is intentionally deferred" — 천문 계산만 수행 |
| `aim/intelligence.py:33` | "기상청 실측 예보(P0) 연동 전에는 금액 산출 불가" |

`aim/kma_weather.py`는 존재하지 않고, `.env`도 `.gitignore`도 없습니다(저장소가 git 미초기화).
이전 작업은 **문서화 단계에서 중단**되었고, 사용자의 기억과 저장소 상태 사이에 차이가 있었습니다.

그래서 doc 13이 지시한 다음 항목인 **P0-3**으로 진행했습니다.

> **P0-3**: `context_engine.py`가 `EnvironmentSignal`을 소비하도록 오버라이드 주입 확장 (기존 코드 파괴 없이)

---

## 2. 조사에서 드러난 결함 3건

P0-3는 "매개변수 하나 추가"로 끝날 줄 알았습니다. 아니었습니다.

### 2.1 결함 A — 아무도 주입하지 않는다 (사소)

`build_context()`는 이미 `env_signal` 매개변수를 받고 있었습니다.
하지만 `AIMPlatform.plan_campaign()`이 그 값을 넘기지 않았고, 호출자는 어디에도 없었습니다.
**문은 있었지만 문을 통과하는 사람이 없던 상태**입니다.

### 2.2 결함 B — 필드가 있어도 아무도 읽지 않는다 (핵심)

결함 A를 고쳐 주입이 가능해져도, 결과는 달라지지 않았습니다.

```python
# 실행 결과 — 동일한 situation 문자열
주입 전: "수 · 11시간 35분 · 추분 · 일몰 18:19 · 15시"
주입 후: "수 · 11시간 35분 · 추분 · 일몰 18:19 · 15시"
```

원인은 `describe_situation()`이 기상 필드를 **한 번도 읽지 않기** 때문입니다.
검증 방법(추측이 아니라 실행으로 확인):

```
temp_c         referenced in describe_situation: False
precip_prob    referenced in describe_situation: False
precip_mm      referenced in describe_situation: False
weather_code   referenced in describe_situation: False
has_weather    referenced in describe_situation: False
```

**이게 이번 스텝의 진짜 내용입니다.** 키가 내일 와도, 필드를 채우는 수집기만 붙이면
결과 문자열은 바이트 단위로 동일했을 것입니다. 고립된 필드는 장식이었습니다.

### 2.3 결함 C — `situation`이 센서 실측을 완전히 가린다 (가장 심각)

```python
base_situation = situation or EnvironmentSensor.describe_situation(signal)
```

`and/or` 단락 평가 때문에 `situation`이 참이면 `describe_situation()`은 **호출조차 되지 않습니다.**
그리고 실제 파이프라인에서는 항상 참입니다:

```python
# aim/core/platform.py (P0-3 이전)
context = ContextEngine.build_context(
    ...,
    situation=state.trigger_event,   # ← 테넌트가 직접 적은 문자열, 항상 비어 있지 않음
)
```

실행으로 확인:

```
state.trigger_event : 오늘 오후 15시 비 예보 + 2시 이후 사워도우 조기 품절
plan.situation      : 오늘 오후 15시 비 예보 + 2시 이후 사워도우 조기 품절
→ describe_situation() 은 이 경로에서 한 번도 호출되지 않는다.
```

**P0-1이 만든 실측 `situation`은 운영 경로에서 단 한 번도 쓰이지 않았습니다.**
문서 14가 "실측화됐다"고 보고한 그 문자열이, 실측 경로에는 없었습니다.

### 2.4 부수 발견: 날짜와 계절의 불일치

`resolve_season()`은 `datetime.now()`를 씁니다. 미래 예보 신호를 주입하면
"12월 22일 신호인데 계절은 가을"처럼 **날짜와 계절이 어긋납니다.**

---

## 3. 설계 판단: 측정이 서술보다 우선한다

### 3.1 선택지

| 선택지 | 판정 |
| :--- | :--- |
| ① `situation`을 계속 최우선으로 두고 기상은 별도 축으로만 전달 | ❌ 6D 벡터에 기상 축이 없어 도메인 플러그인이 못 씁니다. 플러그인은 `context.situation` 문자열만 봅니다. |
| ② `situation`을 무시하고 실측으로 대체 | ❌ 테스트베드 시나리오("기습 첫눈")와 `trigger_event` 서술이 사라집니다. doc 14 §5.3이 보장했던 동작을 깨뜨립니다. |
| ③ **명시적으로 주입된 신호만 사람 문자열을 합쳐 쓴다** | ✅ **채택** |

### 3.2 채택한 규칙

```
주입 없음  →  기존 동작 그대로 (사람 문자열 사용)
주입 있음  →  f"{사람 문자열} · {센서 실측}"
```

측정값과 사람이 쓴 서술은 **양보 관계가 아니라 보강 관계**입니다.
"정기 점검 중"과 "강수확률 80%"는 동시에 사실입니다.
그리고 **주입이 없으면 아무것도 바뀌지 않아야 한다**는 무파괴 조건을 지켰습니다.

이 규칙이 없으면 수집기를 붙이는 순간 측정이 `trigger_event` 문자열에 묻혀
"수집기 없이도 똑같이 도는" 시스템이 됩니다. 지금 그 상태였습니다.

---

## 4. 구현

| 파일 | 변경 |
| :--- | :--- |
| `aim/environment_sensor.py` | `describe_weather()` 신설, `KMA_SKY_WEATHER_CODES` 매핑표, `RAIN_TRIGGER_THRESHOLD`, `_observed_date()`, `_signal_datetime()` |

> **후속 수정 (docs/17)**: 이 스텝의 `KMA_WEATHER_CODES`는 docs/17에서
> `KMA_SKY_WEATHER_CODES`로 개명되었습니다. 기상청 SKY 코드와 WMO 코드가 같은
> 숫자를 다른 뜻으로 쓰기 때문에, 어느 체계인지 이름에 드러내야 하기 때문입니다.
> 하위 호환 별칭 `KMA_WEATHER_CODES`는 남아 있으나 **신규 코드에서는 쓰지 않습니다.**
| `aim/core/context_engine.py` | `_resolve_situation()` 신설(측정>서술), `_observed_instant()`, 계절을 주입 날짜 기준으로 |
| `aim/core/platform.py` | `plan_campaign(env_signal=...)` 주입점 개방 |
| `tests/test_env_signal_injection.py` | 신규 17건 |

### 4.1 기상 코드 매핑표 — 미검증 사항 명시

```python
KMA_SKY_WEATHER_CODES: Dict[str, str] = {
    "0": "맑음", "1": "대략 맑음", "2": "부분적 흐림", "3": "흐림",
    "4": "약한 비", "5": "비", "6": "눈 또는 비", "7": "눈",
    "8": "약한 소나기", "9": "소나기",
}
```

**이 표는 기상청 명세와 대조한 것이 아닙니다.** 통상적 매핑으로 작성했습니다.
(이후 docs/17에서 이 표는 KMA SKY 체계 전용으로 분리되고 WMO 표가 추가됩니다.)
거짓말하지 않기 위해 코드 주석과 본문에 명시했습니다. 표가 틀리면 수정은 **이 상수 하나**이며,
수집기·스키마·테스트는 손대지 않습니다. 매핑되지 않은 코드는 라벨을 지어내지 않고 무시됩니다.

### 4.2 강수확률 문턱값 — 이건 우리의 판정이지 기상청의 권고가 아니다

```python
RAIN_TRIGGER_THRESHOLD = 0.6
```

**근거를 분명히 합니다.** 이 0.6은 기상청 권고가 아니라 **우리 상품의 판정 기준**입니다.
"유휴 방어 캠페인을 사장님 화면에 한 번 더 띄워도 부담이 없다"는 사업 판단입니다.
숫자를 리터럴로 박지 않고 이름 있는 상수로 둔 이유가 이것입니다.

문턱 없이 토큰 매칭만 하면 **강수확률 10%인 맑은 날에 "비 대응 캠페인"을 쏘게 됩니다.**
그건 기상 데이터가 아니라 소음입니다. 문턱 없는 자동화는 가장 비싼 오류를 만듭니다.

---

## 5. 검증 결과

### 5.1 계측 전후 (동일 입력, 유일한 차이는 주입 여부)

```
[미주입]
  situation : 정기 점검 중
  objective : OPPORTUNITY_CAPTURE

[주입: 약한 비 / 강수확률 80% / 시간당 2.5mm / 18도]
  situation : 정기 점검 중 · 수 · 약한 비 강수확률 80% 시간당 2.5mm 18도 · 11시간 35분 · 추분 · 일몰 18:19 · 15시
  objective : CAPACITY_RESCUE          ← FNB 날씨 트리거 실측 데이터로 발동

[주입: 강수확률 10% / 21도]
  situation : 정기 점검 중 · 수 · 강수확률 10% 21도 · 11시간 35분 · 추분 · 일몰 18:19 · 15시
  objective : OPPORTUNITY_CAPTURE      ← 가짜 경보 없음
```

여기서 중요한 것은 세 번째 케이스입니다. **80%와 10%가 같은 결과를 내지 않습니다.**
측정값을 넣는 것과 측정값을 신뢰하는 것은 별개입니다.

### 5.2 계절 정합성

```
[12월 22일 신호 주입]
  season    : 겨울 (대설 진입 0일 전)      ← '가을'이 아님
  situation : 평소 영업 · 화 · 눈 강수확률 90% -4도 · ...   ← 화요일 = 12/22
```

### 5.3 무파괴 증명

```python
# P0-3 이전과 바이트 단위로 동일한가?
"수 · 11시간 35분 · 추분 · 일몰 18:19 · 15시"   # assertEqual로 고정
```

테스트 `test_key_free_path_is_byte_identical_to_before_p0_3`이 이 문자열을 고정하고 있습니다.
키가 없는 경로의 출력이 한 글자라도 바뀌면 테스트가 깨집니다.

### 5.4 테스트 스위트

```
$ python3 -m pytest tests -q
101 passed in 0.82s
```

| 스위트 | 건수 | 상태 |
| :--- | ---: | :--- |
| `test_env_signal_injection.py` (신규) | 17 | P0-3 |
| `test_pos_ledger.py` | 21 | P0-2 (회귀 없음) |
| `test_environment_sensor.py` | 14 | P0-1 (회귀 없음) |
| 기타 기존 스위트 | 49 | 회귀 없음 |

**84 → 101건. 회귀 0.**

---

## 6. 작성 중 발견한 기존 크래시

`describe_situation()`은 `signal.observed_date`를 보호 없이 파싱하고 있었습니다.

```python
# P0-3 이전
today = datetime.strptime(signal.observed_date, "%Y-%m-%d").date()   # ValueError 가능
```

수집기가 관측일을 빈 문자열이나 다른 형식으로 채우면 **크래시가 사장님 화면까지 전파**됩니다.
P0-1이 새웠던 계약을 스스로 지키지 못한 것이었습니다. 형식 오류 시 오늘로 저하하도록 고쳤습니다.

```
기존 경로: 수 · 11시간 · 15시       # 크래시 대신 저하
날짜만 유효: 수 · 11시간 · 00시
```

---

## 7. 남은 작업 (정직한 자기 감사)

| 항목 | 상태 | 비고 |
| :--- | :--- | :--- |
| **기상청 코드 매핑표 미검증** | 🔴 **미완** | 기상청 명세 대조 필요. 틀려도 수정 범위는 상수 하나 |
| **P1-0 실제 수집기 미구현** | ⏸️ 보류 | 인증키 승인 대기. 이번 스텝이 그 경로를 열었다 |
| **키 확보 절차 미정비** | 📋 선행 필요 | `.env` + `.gitignore` 준비, 키 폐기 안내(§8) |
| **기상 축 6D 벡터 부재** | 🔶 구조적 | 기상이 `situation` 문자열에 섞여 들어간다. 플러그인이 **문자열 키워드 매칭**으로 판정 |
| **키워드 부분일치 오탐 위험** | 🔶 **잠재 버그** | 아래 별도 항목 참조 |
| **지역 좌표 미연결** | 📋 P1 | `resolve_region()`은 문자열 매칭. 격자 좌표 기반 실측은 미구현 |

### 7.1 발견했으나 이번 스텝에서 고치지 않은 버그

`FnbDomainPlugin.evaluate_triggers()`는 `situation` 문자열에서 `["비","눈","한파","폭염","우천"]`을
**부분 문자열**로 찾습니다. 테스트베드 데이터를 훑어보니:

```
medical_derma   situation=평일 오후 노쇼 발생으로 인한 고정비 손실 위기   기상키워드=['비']
                                                          ^^^^^^
```

`'비'`는 **고정비**에서 매칭됐습니다. 날씨가 아니라 고정비입니다.
지금까지 `medical`은 자기 플러그인을 쓰고 우연히 터지지 않았을 뿐입니다.
F&B 사업자의 `trigger_event`에 "할인율", "비율", "준비" 같은 단어가 들어가면
**맑은 날에 비 대응 캠페인이 발사됩니다.**

**고치지 않은 이유**: 이번 스텝은 주입 배선이며, 이건 별개의 구조 문제(6D 벡터에 기상 축이 없어서
문자열 매칭에 의존하고 있다)입니다. 외과적 변경 원칙에 따라 우회하지 않고 보고만 합니다.
권장 해결은 `Context6D`에 기상 정보를 별도 필드로 분리하는 것이지만, 이는 스키마 변경이라
승인이 필요합니다.

---

## 8. 총괄 관리자 결론

> *"이번 스텝은 아무것도 추가하지 않았습니다. **있던 것이 동작하게 만들었습니다.***
>
> *기상청 키를 기다리며 6D 컨텍스트의 두 축을 비워둔 것은 설계 실수였습니다(문서 14). 그런데 이번에 더 큰 실수가 하나 더 나왔습니다. 키가 없어도 필드는 이미 스키마에 있었고, 읽는 코드는 한 줄도 없었습니다. **12월 22일 눈 예보를 넣어도 출력은 '추분 · 15시'로 동일했을 것입니다.** 오늘 날씨가 제일 곤란한 건 키가 없다는 게 아니라, 키가 와도 아무도 그 값을 쓰지 않는다는 사실이었을 겁니다.*
>
> *더 놀라운 건 그보다 위에 있었습니다. 실측으로 만든 상황 문자열이 운영 경로에서 **한 번도 실행되지 않았다**는 것입니다. `situation or describe_situation(...)` 한 줄이, 항상 참인 왼쪽 값 때문에 오른쪽을 죽이고 있었습니다. 테스트는 통과했고 화면은 정상인데 그 값은 어디에도 쓰이지 않았습니다. **측정치가 있어도 배선이 없으면 존재하지 않는 것과 같습니다.** 문서 13이 '기존 코드 파괴 없이'라고 지시한 이유를 이제야 이해합니다.*
>
> *그래서 규칙을 하나 세웠습니다. **명시적으로 주입된 신호는 사람이 쓴 문자열보다 우선합니다.** 측정값과 서술은 보강 관계입니다. '정기 점검 중'과 '강수확률 80%'는 동시에 사실이니까요. 그리고 주입이 없으면 아무것도 바꾸지 않습니다. 열쇠가 없어도 예보가 오면 '강수확률 10%'는 그대로 보이되 '비 예보'는 붙지 않습니다. **10%와 80%가 같은 결과를 내는 날은 그 기상 데이터가 아니라 광고입니다.**"*

---

## 9. 차기 액션 아이템

1. **키 확보 절차**: `.env` + `.gitignore` 준비, `.gitignore`에 `.env` 포함
2. **키 폐기(rotate)**: 대화 기록에 평문으로 남은 인증키 폐기 (문서 14 §2.2)
3. **P1-0**: 기상청 단기예보 수집기 — 매핑표 대조 + 격자 좌표 변환 + `env_signal` 주입
4. **구조 개선 승인 요청**: `Context6D`에 기상 축 분리 → 부분일치 오탐 제거 (§7.1)

---

**참조 문서**: [12_multidimensional_data_collection_expert_panel.md](12_multidimensional_data_collection_expert_panel.md) · [13_gate0_data_governance_implementation.md](13_gate0_data_governance_implementation.md) · [14_environment_sensor_p0_1.md](14_environment_sensor_p0_1.md) · [15_p0_2_pos_ledger_implementation.md](15_p0_2_pos_ledger_implementation.md) · [docs/13 §8-3 P0-3](13_gate0_data_governance_implementation.md)
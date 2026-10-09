# AIM — Google Stitch 디자인 토큰 명세서 (tokens.md)

> **디자인 테마**: Calm Ergonomic Dark System (눈이 편안한 인체공학적 다크 테마)  
> **표준 규격**: 2026 Ergonomic Dark UI & APCA(Advanced Perceptual Contrast Algorithm) 가독성 가이드라인 & Calm UI  
> **참조 파일**: [`tokens.css`](file:///Users/ssh/Documents/Develope/AIM/docs/design/tokens.css)  
> **화면 설계 명세**: [`18_google_stitch_ui_screen_design_specification.md`](file:///Users/ssh/Documents/Develope/AIM/docs/18_google_stitch_ui_screen_design_specification.md)

---

## 1. 개요 및 설계 철학

**Calm Ergonomic Dark System(눈이 편안한 인체공학적 다크 테마)**은 다크 모드 특유의 시각적 이점(OLED 배터리 절감, 집중도 향상)은 극대화하면서, 트루 블랙(`#000000`)과 고대비 순백색 텍스트(`#FFFFFF`)가 유발하는 빛 번짐(Halation) 현상 및 장시간 작업 시의 눈 피로감을 최소화하도록 설계된 2026년형 차세대 B2B SaaS 디자인 시스템입니다.

### 핵심 3대 원칙
1. **Halation & Glare 방지 (무결점 차콜 & 오프화이트)**:
   - 배경은 트루 블랙 대신 딥 차콜 슬레이트(`#121417`)를 사용합니다.
   - 텍스트는 순백색 대신 부드러운 오프화이트 소프트 펄(`#E6E8EC`)을 적용하여 눈부심을 원천 차단합니다.
2. **APCA(지각적 대비 알고리즘) 가독성 표준 충족**:
   - 텍스트와 배경 간의 대비를 단순 수치(WCAG 2.x)가 아닌 인간 시각 인지 특성(APCA)에 맞춰 편안하고 명확하게 조율했습니다.
3. **Desaturated Warm Accents (시각적 과자극 배제)**:
   - 공격적인 네온 컬러 대신 따뜻하게 채도를 낮춘 테라코타 오렌지(`#D96B27`)와 차분한 세이지 그린(`#4E9F86`)을 적용하여 인지 부하를 줄였습니다.

---

## 2. 토큰 상세 목록 (Design Tokens)

### 2.1 Surface & Background (표면 계층)

| 토큰명 | CSS 변수 | Hex / RGBA | 디자인 설명 및 APCA 가독성 고려사항 |
| :--- | :--- | :--- | :--- |
| **Main Canvas** | `--surface-canvas` | `#121417` | 메인 배경. 트루 블랙 배제 딥 차콜 슬레이트 |
| **Panel** | `--surface-panel` | `#161A20` | 중간 기둥 패널 배경 |
| **Card (Surface 1)** | `--surface-card` | `#1C2026` | 1단계 컨테이너 (Muted Charcoal Container) |
| **Elevated (Surface 2)** | `--surface-card-elevated` | `#262B33` | 2단계 컨테이너 (호버, 모달, 상위 플로팅 카드) |
| **Input** | `--surface-input` | `#121417` | 폼 입력창, 셀렉트박스 배경 |
| **Border / Divider** | `--surface-border` | `rgba(255, 255, 255, 0.08)` | 1px 은은한 반투명 경계선 (자극 없는 구획 분리) |
| **Border Focus** | `--surface-border-focus` | `#D96B27` | 테라코타 포커스 활성화 테두리 |

### 2.2 Semantic Colors (의미적 색상)

| 토큰명 | CSS 변수 | Hex Code | 용도 및 의미 |
| :--- | :--- | :--- | :--- |
| **Primary Accent** | `--color-primary` | `#D96B27` | 주 액션 버튼(CTA), 브랜드 로고, AI 기안 강조 (Muted Terracotta) |
| **Primary Hover** | `--color-primary-hover` | `#C25B1D` | 버튼 호버 상태 |
| **Success / Active** | `--color-success` | `#4E9F86` | 매출 창출액, ROI 순이익, 실측 사실(`A_MEASURED`), 정상 구독 (Soft Sage Green) |
| **Warning / Caution** | `--color-warning` | `#E5A84B` | 실시간 현안 트리거(비 예보/유휴), 시연값(`C_ILLUSTRATIVE`) (Muted Amber) |
| **Danger / Alert** | `--color-danger` | `#E05D5D` | 법률 위반 차단어, 고위험 격리 카피(`CRITICAL`), 악성 리뷰 (Soft Muted Coral Red) |
| **Purple Accent** | `--color-purple` | `#8B7ED8` | Enterprise 플랜 배지, 총괄 FinOps |
| **Pink Accent** | `--color-pink` | `#D9658B` | 숏폼 크리에이터 마켓플레이스, 인스타그램 릴스 |
| **Cyan Accent** | `--color-cyan` | `#4EA3B8` | 기상/기후 레이더, 옴니채널 사출 엔진 |

### 2.3 Typography & Tabular Numbers (타이포그래피)

| 토큰명 | CSS 변수 | Hex Code | 역할 |
| :--- | :--- | :--- | :--- |
| **Text Primary** | `--text-primary` | `#E6E8EC` | 메인 헤드라인 및 본문 (Off-White Soft Pearl) |
| **Text Secondary** | `--text-secondary` | `#9CA3AF` | 부가 설명, 타임스탬프, 근거 법령 라벨 (Muted Cool Grey) |
| **Text Muted** | `--text-muted` | `#6B7280` | 비활성 캡션 및 메타데이터 |

- **Font Family**: `"Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Tabular Numbers (`font-variant-numeric: tabular-nums`)**:
  - 통장 잔고, 창출 매출(+₩4,320,000), ROI 배수(88.2배) 등 실시간 변동 수치에 적용하여 자릿수 떨림 방지.

### 2.4 Spacing & Border Radius (Bento Grid 8pt 시스템)

- **Spacing**: `4px` (`--space-1`) ~ `48px` (`--space-12`)
- **Radius**:
  - 카드: `14px` (`--radius-lg`) ~ `18px` (`--radius-xl`)
  - 버튼: `10px` (`--radius-md`)
  - 배지/알약: `9999px` (`--radius-full`)

---

## 3. Stitch 화면 매핑

| Stitch 화면 | 대표 적용 토큰 |
| :--- | :--- |
| **Screen 1 (Tenant Cockpit)** | `--surface-card`, `--color-primary`, `--color-success`, `--color-warning` |
| **Screen 2 (Approval Desk)** | `--color-primary`, `--color-success`, `--surface-card-elevated`, `--shadow-glow-primary` |
| **Screen 3 (Attribution Ledger)** | `--color-success`, `--font-tabular`, `--surface-border-light` |
| **Screen 4 (Master Admin)** | `--color-purple`, `--color-warning`, `--surface-panel` |
| **Screen 5 (Quarantine Queue)** | `--color-danger`, `--color-danger-subtle`, `--shadow-glow-danger` |
| **Screen 6 (6D Engine Radar)** | `--color-cyan`, `--color-primary`, `--font-family-mono` |
| **Screen 7 (Business Intro)** | `--color-primary`, `--color-pink`, `--color-success`, `--radius-xl` |
| **Screen 8 (Onboarding 3-Step)** | `--color-success`, `--color-primary`, `--color-warning`, `--radius-lg` |
| **Screen 9 (Creator Escrow)** | `--color-pink`, `--color-purple`, `--color-success` |

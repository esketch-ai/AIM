# AIM — Google Stitch 디자인 토큰 명세서 (tokens.md)

> **디자인 테마**: Deep Cosmic Slate (다크모드 엔터프라이즈 B2B SaaS)  
> **참조 파일**: [`tokens.css`](file:///Users/ssh/Documents/Develope/AIM/docs/design/tokens.css)  
> **화면 설계 명세**: [`18_google_stitch_ui_screen_design_specification.md`](file:///Users/ssh/Documents/Develope/AIM/docs/18_google_stitch_ui_screen_design_specification.md)

---

## 1. 개요

Google Stitch 디자인 토큰은 AIM 마케팅 OS의 모든 UI 컴포넌트(포털, 어드민, 서비스 엔진, 숏폼 크리에이터 데스크)의 시각적 일관성과 유지보수성을 보장하는 핵심 토큰 집합입니다.
기존 HTML 내 50여 개가 넘던 하드코딩 색상을 시맨틱 토큰으로 체계화하여, Linear, Stripe, Vercel 수준의 절제된 고밀도 다크모드 감성을 완성합니다.

---

## 2. 토큰 상세 목록

### 2.1 Surface & Background (표면 계층)

| 토큰명 | CSS 변수 | 값 | 용도 |
| :--- | :--- | :--- | :--- |
| **Canvas** | `--surface-canvas` | `#090D16` | 전체 최하단 캔버스 배경 (Deep Obsidian) |
| **Panel** | `--surface-panel` | `#0D1322` | 대형 기둥 패널 배경 |
| **Card** | `--surface-card` | `#111827` | 기본 데이터 카드, 위젯 표면 (Charcoal Surface) |
| **Elevated** | `--surface-card-elevated` | `#1E293B` | 마우스 호버, 모달, 상위 플로팅 카드 |
| **Input** | `--surface-input` | `#0B0F19` | 폼 입력창, 셀렉트박스 배경 |
| **Border** | `--surface-border` | `#1F2937` | 1px 미세 테두리선 |
| **Border Focus** | `--surface-border-focus` | `#4F46E5` | 포커스 활성화 테두리 |

### 2.2 Semantic Colors (의미적 색상)

| 토큰명 | CSS 변수 | 값 | 용도 |
| :--- | :--- | :--- | :--- |
| **Primary** | `--color-primary` | `#6366F1` | 주 액션 버튼, 브랜드 로고, AI 기안 강조 |
| **Success** | `--color-success` | `#10B981` | 매출 창출액, 순이익 ROI 배수, 실측 사실(`A_MEASURED`), 정상 구독 |
| **Warning** | `--color-warning` | `#F59E0B` | 실시간 현안 트리거(비 예보/유휴), 시연값(`C_ILLUSTRATIVE`) |
| **Danger** | `--color-danger` | `#EF4444` | 컴플라이언스 차단어, 고위험 격리 카피(`CRITICAL`), 1점 악성 리뷰 |
| **Purple** | `--color-purple` | `#8B5CF6` | Enterprise 플랜 배지, 마스터 FinOps |
| **Pink** | `--color-pink` | `#EC4899` | 숏폼 크리에이터 마켓플레이스, 인스타그램 릴스 |
| **Cyan** | `--color-cyan` | `#06B6D4` | 기상/기후 레이더, 옴니채널 사출 엔진 |

### 2.3 Typography & Tabular Numbers (타이포그래피)

- **Font Family**: `"Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Tabular Numbers (`font-variant-numeric: tabular-nums`)**:
  - 통장 잔고, 창출 매출(+₩4,320,000), ROI 배수(88.2배) 등 실시간 변동 수치에 적용하여 자릿수 떨림 방지.

### 2.4 Spacing & Border Radius (8pt 그리드 & 곡률)

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

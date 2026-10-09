# AIM — 공식 디자인 토큰 명세서 (tokens.md)

> **디자인 테마**: Toss Signature Blue & Deep Slate (토스 시그니처 블루 & 딥 슬레이트 테마)  
> **표준 규격**: Toss Visual-First & APCA 가독성 표준  
> **참조 파일**: [`tokens.css`](file:///Users/ssh/Documents/Develope/AIM/docs/design/tokens.css)  
> **핵심 아이덴티티**: 대한민국 핀테크 표준의 강력한 시인성, 시각적 청량감, 극도의 신뢰도  

---

## 1. 개요 및 설계 철학

**Toss Signature Blue & Deep Slate**는 대한민국 골목상권 자영업 사장님들에게 가장 친숙하고 신뢰도가 높은 **토스(Toss) 스타일의 비주얼 퍼스트 체계**입니다.
기존의 탁한 오렌지/브라운 톤을 완전히 배제하고, 눈에 선명하게 들어오는 **Electric Blue (`#3182F6`)**와 청량한 **Toss Mint (`#00C48C`)**, 프리미엄 **Deep Slate Canvas (`#0B0F19`)**를 조화시켜 **3초 만에 핵심 수치를 인지하고 1-Click 의사결정을 완료**할 수 있도록 최적화되었습니다.

### 핵심 3대 원칙
1. **극도의 시인성과 신뢰도 (Toss Signature Blue #3182F6)**:
   - 금융 앱 수준의 높은 신뢰감을 제공하며 1-Click CTA 버튼이 한눈에 들어옵니다.
2. **시각적 청량감과 매출 직관성 (Toss Mint #00C48C)**:
   - "내가 번 돈", "순이익", "실측 검증" 지표를 시원하고 선명한 민트 에메랄드로 표시합니다.
3. **선명한 텍스트 대비 (Crisp White #FFFFFF & Cool Slate #94A3B8)**:
   - 어두운 매장이나 야간 마감 시에도 글자가 뭉개지지 않고 선명하게 읽힙니다.

---

## 2. 디자인 토큰 상세 목록 (Design Tokens)

### 2.1 Surface & Background (표면 계층)

| 토큰명 | CSS 변수 | Hex / RGBA | 디자인 설명 |
| :--- | :--- | :--- | :--- |
| **Main Canvas** | `--surface-canvas` | `#0B0F19` | 메인 캔버스 (Deep Obsidian Slate) |
| **Panel** | `--surface-panel` | `#111827` | 중간 네비게이션 및 패널 |
| **Card (Surface 1)** | `--surface-card` | `#161F30` | 1단계 컨테이너 (Clean Bento Container) |
| **Elevated (Surface 2)** | `--surface-card-elevated` | `#1E293B` | 모달, 플로팅 시트, 호버 카드 |
| **Input** | `--surface-input` | `#0B0F19` | 입력창 배경 |
| **Border / Divider** | `--surface-border` | `rgba(255, 255, 255, 0.08)` | 1px 미세 구분선 |
| **Border Focus** | `--surface-border-focus` | `#3182F6` | 토스 블루 포커스 라인 |

### 2.2 Semantic Colors (의미적 색상)

| 토큰명 | CSS 변수 | Hex Code | 용도 및 의미 |
| :--- | :--- | :--- | :--- |
| **Primary Accent** | `--color-primary` | `#3182F6` | 1-Click 주요 CTA 버튼, 플랫폼 브랜드, 신뢰 (Toss Electric Blue) |
| **Primary Hover** | `--color-primary-hover` | `#1B64DA` | 버튼 호버/프레스 상태 |
| **Success / Revenue** | `--color-success` | `#00C48C` | 창출 매출액, ROI 순이익, 실측 사실(`A_MEASURED`) (Toss Mint) |
| **Warning / Caution** | `--color-warning` | `#F59E0B` | 실시간 현안 트리거(비 예보/유휴), 주의 알림 (Amber) |
| **Danger / Alert** | `--color-danger` | `#EF4444` | 법률 위반 차단, 고위험 격리 심의 (Vibrant Coral Red) |
| **Purple Accent** | `--color-purple` | `#8B5CF6` | 엔터프라이즈, 상권 분석 배지 |
| **Pink Accent** | `--color-pink` | `#EC4899` | 15초 숏폼 크리에이터, 인스타그램 |
| **Cyan Accent** | `--color-cyan` | `#06B6D4` | 기상/기후 인프라 센서 |

### 2.3 Typography & Tabular Numbers

| 토큰명 | CSS 변수 | Hex Code | 역할 |
| :--- | :--- | :--- | :--- |
| **Text Primary** | `--text-primary` | `#FFFFFF` | 메인 헤드라인 및 핵심 수치 (Crisp Pure White) |
| **Text Secondary** | `--text-secondary` | `#94A3B8` | 본문, 서브 라벨, 설명 (Cool Slate Grey) |
| **Text Muted** | `--text-muted` | `#64748B` | 캡션, 타임스탬프 |

* **Font Family**: `"Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
* **Tabular Numbers (`font-variant-numeric: tabular-nums`)**: 변동 금액(+₩4,320,000) 자릿수 흔들림 방지

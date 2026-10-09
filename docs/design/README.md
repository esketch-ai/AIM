# AIM — UI 디자인 참조 및 Google Stitch 연동 자산 (Design Reference)

> **목적**: 이 디렉토리는 **Google Stitch 기반 UI 디자인 산출물의 영속 보관처**입니다.
> 채팅으로 주고받는 링크와 캡처 화면은 다음 세션에서 사라집니다.
> 프로젝트 지침(헤르메스 규칙 §2 상태 영속화)에 따라, 확인된 디자인과 토큰은 이 경로에 완전하게 영속화되었습니다.

---

## 1. 원본 참조

| 항목 | 값 |
| :--- | :--- |
| 도구 | Google Stitch (Google Labs AI-Native Design Canvas, `stitch.withgoogle.com`) |
| 디자인 테마 | Calm Ergonomic Dark System (눈이 편안한 인체공학적 다크 테마) |
| 프로젝트 URL | `https://stitch.withgoogle.com/u/1/projects/7289754663545516650?pli=1` |
| 상세 화면 설계서 | [`docs/18_google_stitch_ui_screen_design_specification.md`](../18_google_stitch_ui_screen_design_specification.md) |
| 화면 가이드 & 프롬프트 | [`stitch_screen_design_guide.md`](../../stitch_screen_design_guide.md) |

---

## 2. 확보된 영속 디자인 산출물 (Secured Assets)

Google Stitch의 설계 토큰 및 화면 명세가 프로덕션 코드로 100% 확보 및 구현되었습니다:

| 파일/디렉토리 | 설명 | 상태 |
| :--- | :--- | :--- |
| [`21_design_brief_and_rfp.md`](21_design_brief_and_rfp.md) | **디자인 전문팀 의뢰서 및 RFP (플랫폼 개요 & UI/UX 브리프)** | ✅ **작성 완료** |
| [`tokens.css`](tokens.css) | Google Stitch CSS 커스텀 프로퍼티 디자인 토큰 | ✅ **확보 완료** |
| [`tokens.md`](tokens.md) | 색상·폰트·간격(8pt)·그림자 토큰 상세 명세서 | ✅ **확보 완료** |
| [`stitch-export/`](stitch-export/index.html) | Google Stitch 9대 프로덕션 화면 독립 HTML+CSS 세트 | ✅ **확보 완료** |
| `screenshots/` | 주요 화면 시각 자료 및 프리뷰 링크 | ✅ **확보 완료** |

---

## 3. Google Stitch 9대 핵심 화면 구성 체계

모든 화면은 [`stitch-export/index.html`](stitch-export/index.html) 갤러리를 통해 개별 확인 및 통합 포털과 연동됩니다:

1. **[Screen 1] 유료 가입자 매장 관제 총괄 작전실 ([`screen1_tenant_cockpit.html`](stitch-export/screen1_tenant_cockpit.html))**:
   - 매장 사장님 전용 콕핏, 플릿 전환기, WTP 가치 귀속 원장(+432만 원, ROI 88.2배), 실시간 현안 트리거 알림.
2. **[Screen 2] AI 기안 캠페인 승인 데스크 & 폰 프리뷰 ([`screen2_approval_desk.html`](stitch-export/screen2_approval_desk.html))**:
   - 3대 채널 카피 검사, 공정위 표시광고법 제3조 사전 심의 통과, 스마트폰 디바이스 목업 실시간 프리뷰.
3. **[Screen 3] 가치 귀속 원장 & 구독 빌링 정산 ([`screen3_attribution_ledger.html`](stitch-export/screen3_attribution_ledger.html))**:
   - 누적 창출 매출, 납부 구독료, 실효 ROI 배수(46.5배), 캠페인별 상세 원장 표(CSV 다운로드), 결제 카드 관리.
4. **[Screen 4] 플랫폼 총괄 관제 & 플릿 FinOps 워룸 ([`screen4_master_admin.html`](stitch-export/screen4_master_admin.html))**:
   - 전사 4대 KPI(활성 플릿 100%, MRR ₩545,000, GMV +₩145.5M, 평균 ROI 44.5배), 5개사 플릿 관제 그리드, 에이전트 헬스.
5. **[Screen 5] 고위험 광고 카피 인적 검토/격리 큐 ([`screen5_quarantine_queue.html`](stitch-export/screen5_quarantine_queue.html))**:
   - 의료법 제56조 및 표시광고법 위반 고위험 카피 차단, 원문 vs AI 수정안 Side-by-Side Diff 비교 심의 데스크.
6. **[Screen 6] 6D 하이퍼 컨텍스트 서비스 실행 콘솔 ([`screen6_context_radar.html`](stitch-export/screen6_context_radar.html))**:
   - 시대·상황·계절·세대·지역·계기 6차원 환경 벡터 실시간 수집 및 5대 산업군 테스트베드 시뮬레이터.
7. **[Screen 7] 사업주 중심 직관적 서비스 소개 & 가치 랜딩 ([`screen7_business_intro.html`](stitch-export/screen7_business_intro.html))**:
   - 월 4.9만원 가치 제안, 3대 실질 이득(유휴 방어, 기획공수 제로, 15초 숏폼), 투명 요금제, 실시간 ROI 계산기.
8. **[Screen 8] 가입 후 시작하기 3단계 온보딩 로드맵 ([`screen8_onboarding_roadmap.html`](stitch-export/screen8_onboarding_roadmap.html))**:
   - 1단계(채널 1분 연동 완료) ➔ 2단계(AI 24시간 자율 감시 가동 중) ➔ 3단계(오늘 할 일 1건 원클릭 승인).
9. **[Screen 9] 15초 숏폼 바이럴 브리프 & 크리에이터 에스크로 ([`screen9_creator_escrow.html`](stitch-export/screen9_creator_escrow.html))**:
   - 필수 3문항 입력 ➔ 15초 쇼츠 4씬 콘티 ➔ 오디언스 일치율 상위 크리에이터 10% 우대 에스크로 의뢰.

---

## 4. 백엔드 REST API와의 1:1 데이터 연동 보장

Stitch에서 생성된 UI는 AIM 백엔드의 실제 REST 엔드포인트와 오차 없이 직결됩니다:

| 화면 | 주요 바인딩 엔드포인트 | 반환 데이터 및 역할 |
| :--- | :--- | :--- |
| **Screen 1** (Cockpit) | `GET /api/v1/tenant/{id}` | 테넌트 기본 정보, 실시간 현안 트리거, 누적 창출 매출 |
| **Screen 2** (Approval Desk) | `GET /api/v1/tenant/{id}/staged-campaigns`<br>`POST /api/v1/tenant/campaign/{id}/approve` | AI 기안 목록, 3대 채널 카피 프리뷰, 원클릭 송출 집행 |
| **Screen 3** (Attribution Ledger) | `GET /api/v1/tenant/{id}/billing` | 구독료 대비 캠페인별 순이익 원장, 월별 인보이스 내역 |
| **Screen 4** (Master Admin) | `GET /api/v1/admin/overview`<br>`GET /api/v1/admin/fleet/metrics` | 5대 테넌트 계정 플릿, 전사 MRR/ARR/ARPU, 워커 헬스 |
| **Screen 5** (Quarantine Queue) | `GET /api/v1/admin/quarantine`<br>`POST /api/v1/admin/quarantine/{id}/resolve` | 의료법/표시광고법 위반 고위험 카피 심의 및 수동 승인 |
| **Screen 6** (6D Engine Radar) | `GET /api/v1/service/industries`<br>`POST /api/v1/service/simulate` | 6차원 컨텍스트 벡터, 5대 산업군 시뮬레이션 |
| **Screen 7~9** (Intro/Onboard/Creator) | `POST /api/v1/creator/brief/generate`<br>`POST /api/v1/creator/match`<br>`POST /api/v1/orchestrator/trigger` | 15초 브리프 생성, 크리에이터 매칭, 실시간 옴니채널 오케스트레이션 |
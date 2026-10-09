# AIM — Google Stitch 프롬프트 팩 & 핵심 모바일 컴포넌트 레이아웃 명세서

> **문서 번호**: 22  
> **테마 표준**: Toss Signature Blue & Deep Slate (토스 스타일 핀테크 표준 다크 테마)  
> **대상 사용자**: 40~60대 골목상권 자영업 사장님 (요식업, 카페, 뷰티, 소매업)  
> **디자인 목표**: 극도의 시인성과 신뢰도, 3초 인지, 1-Click 의사결정 끝장 UI  
> **연관 파일**: [`tokens.css`](tokens.css), [`tokens.md`](tokens.md), [`21_design_brief_and_rfp.md`](21_design_brief_and_rfp.md)  

---

## 1. Google Stitch 전용 프롬프트 팩 (Screen Prompt Pack)

Google Stitch(`stitch.withgoogle.com`) 캔버스에 그대로 입력하여 고품질 인체공학적 UI를 생성할 수 있는 정밀 프롬프트 구조입니다.

### [Prompt 1] 모바일 사장님 데일리 콕핏 (Today's Action Cockpit - 390px Mobile)

```text
Design a hyper-focused mobile screen (width: 390px) for a local small business owner (restaurant/cafe) called "AIM Daily Action Cockpit".

[Design Theme & Visual Vibe]:
- Toss Signature Blue & Deep Slate (Fintech high-trust standard).
- Main Canvas: Deep Obsidian Slate (#0B0F19).
- Containers & Cards: Clean Bento Container (#161F30) with subtle border rgba(255, 255, 255, 0.08).
- Elevated Container: #1E293B.
- Primary Accent & CTA: Toss Electric Blue (#3182F6, hover #1B64DA).
- Success & Revenue Accent: Toss Mint / Emerald (#00C48C).
- Warning & Trigger Badge: Vibrant Amber (#F59E0B).
- Typography: Pretendard, Pure White text (#FFFFFF) for headlines, Cool Slate Grey (#94A3B8) for subtext. Tabular numbers enabled.
- Grid: 8pt Bento Grid system, card corner radius 16px, button radius 12px. Minimum touch target 48x48px.

[Header Section]:
- Store title: "성수 골목파전 (성수점) ▾" with online green dot indicator.
- Infrastructure Signal Bar (Horizontal pill badges):
  - Badge 1 (Amber): "🌧️ 오늘 15:00 비 예보 (강수확률 85%)"
  - Badge 2 (Sage): "🎪 성수 팝업스토어 거리 유동인구 +42% 급증"

[Hero Card - The Single Daily Action]:
- Top badge: "💡 오늘 AI 추천 행동 (단 1개)"
- Big Bold Headline (20px, Off-white): "비 오는 오후 3시, '해물파전 + 막걸리 세트' 네이버·인스타에 홍보할까요?"
- Rationale callout (14px, Grey): "비 올 때 전 메뉴 검색량 3.8배 상승 중! 주변 오피스 직장인 타겟 추천."
- Primary Action Button (Toss Electric Blue #3182F6, 52px height, full width):
  "👉 1초 만에 내용 확인하고 올리기"

[Secondary Card - Revenue & Proof Summary]:
- Card title: "이번 주 AIM이 벌어다 준 돈"
- Big metric in Toss Mint (28px, Bold, Tabular): "+₩380,000"
- Subtext: "네이버 쿠폰 손님 16명 방문 · 실효 ROI 32.4배"

[Bottom Bar]:
- Minimal 3-item navigation: [홈 콕핏 (Active)] | [성과 영수증] | [설정]
```

---

### [Prompt 2] 1-Click 캠페인 확인 및 자동 배포 바텀시트 (1-Click Approval Sheet)

```text
Design an intuitive mobile bottom-sheet modal screen (width: 390px) for "AIM 1-Click Multi-Channel Multi-Publishing Preview".

[Design Theme & Visual Vibe]:
- Background modal overlay: rgba(11, 15, 25, 0.8) with backdrop-blur.
- Elevated Sheet Container: #1E293B (Surface Card Elevated), top rounded corners 24px, 1px border rgba(255, 255, 255, 0.12).
- Primary Button: Toss Signature Electric Blue (#3182F6) with subtle bright glow.
- Compliance Verified Badge: Toss Mint (#00C48C).
- Text: Crisp Pure White (#FFFFFF) and Cool Slate Grey (#94A3B8).

[Header]:
- Drag handle bar at top center.
- Title: "AI가 작성한 오늘 홍보 콘텐츠"
- Verified Badge: "✓ 공정위 광고 심의 통과 (표시광고법 준수)" in Toss Mint pill.

[Channel Selector Tabs]:
- Segmented control pills: [🟢 네이버 스마트플레이스 (Active)] | [🟣 인스타그램 피드] | [🥕 당근 비즈프로필]

[Live Preview Card]:
- Realistic mock rendering of Naver Smart Place Post / Instagram Feed.
- Image: High quality hot crispy Seafood Pajeon on traditional Korean plate.
- Headline: "비 오는 성수동, 바삭한 해물파전과 함께 빗소리 즐기세요 🌧️"
- Body: "오늘 오후 3시부터 7시까지 비 오는 날 특별 10% 막걸리 페어링 쿠폰을 드립니다. (네이버 예약 시 자동 적용)"
- Tags: #성수동맛집 #비오는날파전 #성수역막걸리

[Bottom Sticky Action Area]:
- Single massive primary CTA button (Height: 56px, Radius: 14px, Toss Blue #3182F6):
  "🚀 [지금 1초 만에 세 곳 동시 올리기]"
- Helper caption below button (12px, Muted Grey): "클릭 즉시 네이버, 인스타, 당근마켓에 동시 배포됩니다."
```

---

### [Prompt 3] 가치 검증 모바일 영수증 리포트 (Attribution Ledger Sheet)

```text
Design a paper-receipt inspired mobile report screen (width: 390px) called "AIM Value Proof Ledger".

[Design Theme & Visual Vibe]:
- Toss Signature Blue & Deep Slate. Canvas: #0B0F19.
- Receipt Container: #161F30 with jagged/torn paper top and bottom edges (perforated receipt visual motif), subtle border rgba(255, 255, 255, 0.08).
- Font: Pretendard with monospaced tabular numerals (font-variant-numeric: tabular-nums).
- Accents: Toss Mint (#00C48C) for positive ROI, Toss Blue (#3182F6) for subscription comparison.

[Receipt Header]:
- Title: "🧾 이번 달 AIM 투자 & 실적 영수증"
- Period: "2026.10.01 ~ 2026.10.09 (9일간 집계)"

[Core Comparison Block]:
- "월 구독료 투자": ₩49,000 (Muted Grey)
- "AIM 창출 실매출": "+₩4,320,000" (Bold 28px Toss Mint #00C48C)
- "실효 수익 배수": "88.2배 (순수익 427만 원 창출)"

[Breakdown List]:
- Item 1: "10/03 비 예보 파전 프로모션 ➔ 손님 24팀 (+₩680,000)"
- Item 2: "10/05 성수 팝업 금요 퇴근길 특가 ➔ 손님 38팀 (+₩1,240,000)"
- Item 3: "10/08 당근마켓 동네 첫방문 쿠폰 ➔ 단골 전환 19명 (+₩420,000)"

[Bottom Proof Barcode & Guarantee]:
- POS 실측 연동 바코드 그래픽 및 "✓ 신한/포스 실측 영수증 검증 완료" 공식 인증 마크.
```

---

## 2. 핵심 모바일 화면(P0) 3종 컴포넌트 레이아웃 명세 & HTML/CSS 코드

아래 코드는 디자인팀 및 개발팀이 즉시 브라우저나 모바일 뷰어에서 렌더링하고 커스텀할 수 있는 **프로덕션 수준의 시맨틱 HTML/CSS 컴포넌트**입니다.

### 2.1 [Screen 1] 사장님 데일리 콕핏 컴포넌트

```html
<!-- Screen 1: Mobile Cockpit (390px) -->
<div class="mobile-frame" style="max-width: 390px; margin: 0 auto; background: var(--surface-canvas); color: var(--text-primary); font-family: 'Pretendard', sans-serif; min-height: 100vh; padding: 20px 16px;">
  
  <!-- Store Header -->
  <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
    <div>
      <span style="font-size: 13px; color: var(--text-secondary);">자율 운영 콕핏</span>
      <h1 style="font-size: 18px; font-weight: 700; margin: 2px 0 0; display: flex; align-items: center; gap: 6px;">
        성수 골목파전 <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--color-success);"></span>
      </h1>
    </div>
    <div style="background: var(--surface-card); border: 1px solid var(--surface-border); border-radius: 20px; padding: 6px 12px; font-size: 12px; color: var(--text-secondary);">
      AI 24H 감시 중
    </div>
  </header>

  <!-- Infrastructure Signal Badges -->
  <div style="display: flex; gap: 8px; overflow-x: auto; margin-bottom: 20px; padding-bottom: 4px;">
    <div style="background: rgba(229, 168, 75, 0.15); border: 1px solid var(--color-warning); border-radius: 20px; padding: 6px 12px; font-size: 12px; color: var(--color-warning); white-space: nowrap;">
      🌧️ 15시 비 예보 (85%)
    </div>
    <div style="background: rgba(78, 159, 134, 0.15); border: 1px solid var(--color-success); border-radius: 20px; padding: 6px 12px; font-size: 12px; color: var(--color-success); white-space: nowrap;">
      🎪 성수 팝업 유동인구 +42%
    </div>
  </div>

  <!-- Hero Card: Single Daily Recommendation -->
  <div style="background: var(--surface-card); border: 1px solid var(--surface-border); border-radius: 18px; padding: 20px; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
    <div style="display: inline-block; background: rgba(217, 107, 39, 0.2); color: var(--color-primary); padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; margin-bottom: 12px;">
      💡 오늘 AI 추천 행동 (단 1개)
    </div>
    <h2 style="font-size: 19px; font-weight: 700; line-height: 1.4; margin-bottom: 8px; color: var(--text-primary);">
      비 오는 오후 3시, "해물파전 + 막걸리 세트"를 네이버와 인스타에 홍보할까요?
    </h2>
    <p style="font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 20px;">
      비 예보 시간대에 파전 검색량이 평소 대비 3.8배 급증합니다. 성수동 인근 오피스 직장인을 타겟으로 자동 홍보를 진행합니다.
    </p>

    <!-- 1-Click Action Button -->
    <button style="width: 100%; min-height: 52px; background: var(--color-primary); color: #FFFFFF; border: none; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 8px; transition: background 0.2s;" onmouseover="this.style.background='var(--color-primary-hover)'" onmouseout="this.style.background='var(--color-primary)'">
      👉 1초 만에 내용 확인하고 올리기
    </button>
  </div>

  <!-- Value Proof Summary Card -->
  <div style="background: var(--surface-card); border: 1px solid var(--surface-border); border-radius: 18px; padding: 18px; margin-bottom: 24px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
      <span style="font-size: 13px; color: var(--text-secondary);">이번 주 AIM 자동 홍보로 번 돈</span>
      <span style="font-size: 12px; color: var(--color-success); font-weight: 600;">실시간 집계</span>
    </div>
    <div style="font-size: 28px; font-weight: 800; color: var(--color-success); font-variant-numeric: tabular-nums; margin-bottom: 4px;">
      +₩380,000
    </div>
    <div style="font-size: 12px; color: var(--text-secondary);">
      쿠폰 방문 손님 16팀 · 지출 구독료 대비 ROI 32.4배
    </div>
  </div>

  <!-- Bottom Navigation -->
  <nav style="display: flex; justify-content: space-around; background: var(--surface-panel); border: 1px solid var(--surface-border); border-radius: 24px; padding: 12px 8px;">
    <div style="color: var(--color-primary); font-weight: 700; font-size: 13px; text-align: center;">⚡ 오늘 콕핏</div>
    <div style="color: var(--text-secondary); font-size: 13px; text-align: center;">🧾 성과 영수증</div>
    <div style="color: var(--text-secondary); font-size: 13px; text-align: center;">⚙️ 설정</div>
  </nav>

</div>
```

---

### 2.2 [Screen 2] 1-Click 캠페인 확인 및 자동 배포 바텀시트

```html
<!-- Screen 2: 1-Click Multi-Publishing Sheet (390px) -->
<div class="bottom-sheet" style="max-width: 390px; margin: 0 auto; background: var(--surface-card-elevated); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px 24px 0 0; color: var(--text-primary); font-family: 'Pretendard', sans-serif; padding: 16px 20px 32px; box-shadow: 0 -8px 32px rgba(0,0,0,0.5);">
  
  <!-- Drag Handle -->
  <div style="width: 40px; height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; margin: 0 auto 16px;"></div>

  <!-- Header & Compliance Tag -->
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
    <h3 style="font-size: 17px; font-weight: 700; margin: 0;">AI 자동 생성 홍보글</h3>
    <span style="background: rgba(78, 159, 134, 0.2); color: var(--color-success); font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 12px;">
      ✓ 공정위 광고 심의 통과
    </span>
  </div>

  <!-- Channel Selectors -->
  <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 16px;">
    <button style="padding: 8px 4px; background: var(--surface-card); border: 1px solid var(--color-primary); color: var(--color-primary); border-radius: 10px; font-size: 12px; font-weight: 700; cursor: pointer;">
      네이버 플레이스
    </button>
    <button style="padding: 8px 4px; background: var(--surface-card); border: 1px solid var(--surface-border); color: var(--text-secondary); border-radius: 10px; font-size: 12px; cursor: pointer;">
      인스타그램 피드
    </button>
    <button style="padding: 8px 4px; background: var(--surface-card); border: 1px solid var(--surface-border); color: var(--text-secondary); border-radius: 10px; font-size: 12px; cursor: pointer;">
      당근 비즈프로필
    </button>
  </div>

  <!-- Live Mock Preview Box -->
  <div style="background: var(--surface-canvas); border: 1px solid var(--surface-border); border-radius: 14px; padding: 14px; margin-bottom: 20px;">
    <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">[네이버 플레이스 소식 탭 실제 등록 모습]</div>
    <div style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
      비 오는 성수동, 바삭한 해물파전과 빗소리 즐기세요 🌧️
    </div>
    <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 10px;">
      오늘 오후 3시부터 비 오는 날 특별 10% 막걸리 페어링 쿠폰을 드립니다. 네이버 예약 방문 시 자동 적용됩니다.
    </div>
    <div style="height: 110px; background: #262B33; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 12px;">
      [고해상도 바삭 파전 AI 이미지 첨부 완료]
    </div>
  </div>

  <!-- Sticky Single Action Button -->
  <button style="width: 100%; min-height: 56px; background: var(--color-primary); color: #FFFFFF; border: none; border-radius: 14px; font-size: 17px; font-weight: 800; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 8px; box-shadow: 0 4px 16px rgba(217, 107, 39, 0.4);">
    🚀 지금 1초 만에 세 곳 동시 올리기
  </button>
  <p style="text-align: center; font-size: 12px; color: var(--text-muted); margin: 8px 0 0;">
    버튼 클릭 즉시 네이버·인스타·당근마켓에 자동으로 게시됩니다.
  </p>

</div>
```

---

### 2.3 [Screen 3] 초간단 가치 검증 영수증 리포트

```html
<!-- Screen 3: Value Proof Receipt (390px) -->
<div class="receipt-frame" style="max-width: 390px; margin: 0 auto; background: var(--surface-card); border: 1px dashed rgba(255, 255, 255, 0.18); border-radius: 16px; color: var(--text-primary); font-family: 'Pretendard', sans-serif; padding: 24px 20px;">
  
  <!-- Receipt Header -->
  <div style="text-align: center; border-bottom: 1px dashed var(--surface-border); padding-bottom: 16px; margin-bottom: 16px;">
    <div style="font-size: 12px; color: var(--text-secondary); letter-spacing: 2px;">OFFICIAL VALUE PROOF</div>
    <h2 style="font-size: 20px; font-weight: 800; margin: 4px 0 0;">AIM 성과 영수증</h2>
    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">2026.10.01 ~ 2026.10.09 (9일간)</div>
  </div>

  <!-- Comparison Summary -->
  <div style="background: var(--surface-canvas); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
    <div style="display: flex; justify-content: space-between; font-size: 13px; color: var(--text-secondary); margin-bottom: 6px;">
      <span>투자한 월 구독료</span>
      <span style="font-variant-numeric: tabular-nums;">₩49,000</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: baseline; border-top: 1px solid var(--surface-border); padding-top: 8px;">
      <span style="font-size: 14px; font-weight: 700; color: var(--text-primary);">AIM 창출 순매출</span>
      <span style="font-size: 24px; font-weight: 800; color: var(--color-success); font-variant-numeric: tabular-nums;">+₩4,320,000</span>
    </div>
    <div style="text-align: right; font-size: 12px; color: var(--color-success); margin-top: 2px; font-weight: 600;">
      ROI 88.2배 (순이익 427만 원 창출)
    </div>
  </div>

  <!-- Detailed Proof Items -->
  <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.8; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between;">
      <span>• 10/03 비 예보 파전 프로모션</span>
      <strong style="color: var(--text-primary); font-variant-numeric: tabular-nums;">+₩680,000</strong>
    </div>
    <div style="display: flex; justify-content: space-between;">
      <span>• 10/05 성수 팝업 퇴근길 특가</span>
      <strong style="color: var(--text-primary); font-variant-numeric: tabular-nums;">+₩1,240,000</strong>
    </div>
    <div style="display: flex; justify-content: space-between;">
      <span>• 10/08 당근마켓 단골 쿠폰</span>
      <strong style="color: var(--text-primary); font-variant-numeric: tabular-nums;">+₩420,000</strong>
    </div>
  </div>

  <!-- POS Verification Stamp -->
  <div style="border-top: 1px dashed var(--surface-border); padding-top: 14px; display: flex; justify-content: space-between; align-items: center;">
    <span style="font-size: 11px; color: var(--text-muted);">POS 연동 번호: #POS-202610-8841</span>
    <span style="border: 1px solid var(--color-success); color: var(--color-success); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">
      실측 검증 완료
    </span>
  </div>

</div>
```

---

## 3. 디자인팀 및 프론트엔드 연동 체크리스트

1. **Stitch 캔버스 렌더링**: 위 [Prompt 1], [Prompt 2], [Prompt 3] 텍스트를 `stitch.withgoogle.com`에 입력하여 AI 원형 컴포넌트 생성.
2. **토큰 검증**: `--surface-canvas: #0B0F19`, `--color-primary: #3182F6`, `--color-success: #00C48C`이 올바르게 맵핑되었는지 점검.
3. **가독성 점검 (APCA)**: 40~60대 점주 기준 본문 글자 크기가 최소 15px 이상인지, 터치 영역이 48px 이상인지 확인.

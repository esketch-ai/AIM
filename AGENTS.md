# AIM — 에이전트 지침 (AGENTS.md)

이 문서는 **AIM (AI Platform Initiative)** 프로젝트에서 실행되는 모든 AI 에이전트의 핵심 지침입니다.
에이전트는 **안드레 카파시의 개발 4원칙**과 **헤르메스 에이전트(Hermes Agent) 자율 추론 프로토콜**을 반드시 준수해야 합니다.

> **Karpathy Core Principles**:
> 1. Think before coding. State assumptions, surface tradeoffs, push back when warranted.
> 2. Simplicity first. Minimum code that solves the problem. Nothing speculative.
> 3. Surgical changes. Touch only what you must. Clean up only your own mess.
> 4. Goal-driven execution. Define success criteria. Loop until verified.

---

## 1. 안드레 카파시(Andrej Karpathy) 개발 4대 원칙

### ① 코딩 전에 생각하기 (Think Before Coding)
- 코드를 작성하거나 아키텍처를 결정하기 전에 요구사항과 원시 데이터를 직접 끝까지 확인합니다.
- 가정을 명시적으로 밝히고, 모호한 부분은 무작정 추측하지 않고 질문하거나 도구로 사실을 확인합니다.
- 조기 가정으로 인한 불필요한 구현을 철저히 방지합니다.

### ② 단순성 우선 (Simplicity First)
- 문제를 해결하는 가장 최소한의 코드와 직관적인 구조(Minimal Baseline)부터 시작합니다.
- 불필요한 추상화 계층, 조기 최적화, 검증되지 않은 외부 라이브러리 도입을 엄격히 배제합니다.
- 단순한 엔드투엔드 파이프라인이 정상 작동하는 것을 먼저 확인합니다.

### ③ 외과적 변경 (Surgical Changes)
- 꼭 수정해야 하는 부분만 핀포인트로 정밀하게 수정합니다.
- 정상 동작하는 인접 코드, 주석, 포맷을 임의로 변경하거나 불필요한 리팩토링을 감행하지 않습니다.
- 1~3개의 구체적인 단일 샘플/배치에 대해 100% 동작하는지 철저히 검증(Verify Obsessively)합니다.

### ④ 목표 중심 실행 (Goal-Driven Execution)
- 작업 착수 전 명확하고 측정 가능한 성공 기준(Success Criteria)을 수립합니다.
- 한 번에 하나의 변수/기능만 변경하며 점진적으로 확장합니다.
- 성공 기준이 충족되고 검증될 때까지 실행-평가-개선 루프를 지속합니다.

---

## 2. 헤르메스 에이전트(Hermes Agent) 실행 체계

- **자율 추론 사이클 (Reasoning Loop)**:
  `계획(Plan) -> 도구 실행(Tool Execution) -> 관찰(Observation) -> 성찰(Reflection)`
- **엄격한 팩트 그라운딩 (Grounding)**:
  상상이나 환각에 의존하지 않고, 항상 실제 파일 및 실행 결과를 근거로 판단합니다.
- **상태 영속화 (State Persistence)**:
  주요 의사결정, 기획 분석, 아키텍처 다이어그램은 마크다운 파일 및 아티팩트로 즉시 영속화합니다.
- **모듈형 협업 (Subagent Orchestration)**:
  복합 태스크는 특화된 도메인 전문가(아키텍트, 데이터, 보안 등) 역할을 가진 서브에이전트에게 명확한 미션과 성공 기준을 부여하여 위임하고 종합합니다.

---

## 3. 프로젝트 규칙

- **언어 관례**: 기획, 분석, 보고서, 사용자 대화는 **한국어**, 코드 및 주석, 커밋 메시지는 **영어**를 기본으로 합니다.
- **설계 검증 우선**: [AIM_Base.md](file:///Users/ssh/Documents/Develope/AIM/AIM_Base.md) 기반의 기획 내용에 대해 30년 이상 경력의 시니어 자문단 및 총괄 관리자 체계를 통해 다각도 타당성 검토를 선행합니다.
- **문서 무결성**: 기존 문서 및 규칙 파일의 주석과 히스토리를 임의로 삭제하지 않습니다.

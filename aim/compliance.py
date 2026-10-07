"""AIM (AI Platform Initiative) - Compliance & Legal Guardrail
Two-tier deterministic compliance filter to detect and sanitize violations of
the Korean Fair Labeling and Advertising Act (표시광고법) and exaggerated claims.
"""

import re
from typing import List, Tuple, Dict
from aim.schema import ComplianceViolation, ComplianceReport


# Prohibited and restricted phrases database under Korean Advertising Regulations
REGULATED_TERMS: Dict[str, Dict[str, str]] = {
    # 1. Unsubstantiated Superlatives (객관적 실증 없는 절대적/최상급 표현)
    "최고": {
        "category": "객관적 실증 없는 최상급 표현 (표시광고법 제3조 위반 위험)",
        "severity": "HIGH",
        "recommended": "정성을 다한",
        "reason": "공식 기관의 인증이나 객관적 실증 데이터 없이 '최고' 단독 사용 불가"
    },
    "최강": {
        "category": "절대적 우위 과장 표현",
        "severity": "HIGH",
        "recommended": "깊은 풍미를 자랑하는",
        "reason": "소비자 오인 유발 가능 표현"
    },
    "1위": {
        "category": "출처 불분명 순위 표기 (표시광고법 제3조 위반 위험)",
        "severity": "HIGH",
        "recommended": "인기 베스트",
        "reason": "조사 기간, 조사 기관, 표본 수가 명시되지 않은 1위 표기 금지"
    },
    "국내 유일": {
        "category": "배타적 유일성 표현",
        "severity": "HIGH",
        "recommended": "차별화된 레시피의",
        "reason": "전수 조사를 거치지 않은 '유일' 표기 금지"
    },
    "100% 보장": {
        "category": "단정적 확신 및 과대 보증",
        "severity": "HIGH",
        "recommended": "정성을 다해 약속드리는",
        "reason": "불확실한 미래 결과에 대한 단정적 보장 금지"
    },
    "완벽": {
        "category": "절대적 표현",
        "severity": "MEDIUM",
        "recommended": "조화로운",
        "reason": "완전무결성을 보장하는 절대적 수식어 지양 권고"
    },
    # 2. Slang / Inappropriate Ad Expression (비속어 및 품위 저해 표현)
    "미쳤어요": {
        "category": "광고 심의 부적합 구어체/과장 표현",
        "severity": "MEDIUM",
        "recommended": "감탄이 절로 나오는",
        "reason": "광고 매체 심의 및 정중한 브랜드 보이스 유지 권고"
    },
    "극락": {
        "category": "종교적/과장성 은어 표현",
        "severity": "MEDIUM",
        "recommended": "특별한 미식 경험",
        "reason": "대중 매체 광고 가이드라인 준수"
    }
}


class ComplianceGuard:
    """Audits generated marketing copy for regulatory compliance and brand safety."""

    @classmethod
    def audit_text(cls, text: str) -> ComplianceReport:
        violations: List[ComplianceViolation] = []
        sanitized = text

        for term, meta in REGULATED_TERMS.items():
            # Match term as substring
            pattern = re.compile(re.escape(term))
            matches = pattern.findall(text)
            if matches:
                violations.append(
                    ComplianceViolation(
                        original_term=term,
                        rule_category=meta["category"],
                        severity=meta["severity"],
                        recommended_term=meta["recommended"],
                        reason=meta["reason"]
                    )
                )
                # Replace with recommended term in sanitized version
                sanitized = pattern.sub(meta["recommended"], sanitized)

        is_compliant = len(violations) == 0
        return ComplianceReport(
            is_compliant=is_compliant,
            violations=violations,
            original_text=text,
            sanitized_text=sanitized
        )

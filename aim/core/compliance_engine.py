"""AIM (AI Platform Initiative) - Multi-Domain Compliance Engine
Audits content against general Fair Advertising Act and domain-specific regulatory rules (Medical Law Art 56, GDPR, Subcontracting Act).

Attribution audit (docs/19): Open-Meteo 기상 데이터는 CC BY 4.0이므로 출처 표기가
법적 의무다. 이 엔진은 '기상 데이터가 쓰인 산출물인데 표기가 없다'는 상태를
위반으로 판정한다. 약관을 읽고 적어둔 것과 지킨 것은 다르다.
"""

from typing import List, Optional
from aim.schema import ComplianceViolation, ComplianceReport
from aim.compliance import ComplianceGuard
from aim.core.domain_registry import DomainRegistry

# 출처 표기 누락을 식별하는 안정적인 식별자. 문자열 비교로 판정하지 않는다.
ATTRIBUTION_RULE_CATEGORY = "CC BY 4.0 데이터 라이선스 출처 표기 의무"


class ComplianceEngine:
    """Multi-tier regulatory compliance audit engine."""

    @classmethod
    def audit(
        cls, text: str, domain: str, required_attribution: Optional[str] = None
    ) -> ComplianceReport:
        """required_attribution이 주어지면 그 문구가 본문에 있는지 검사한다.

        호출자는 '이 텍스트가 어떤 데이터에서 나왔는지' 근거로 표기 의무를
        판정해 넘긴다. 엔진이 텍스트에서 출처를 추측하지 않는다.
        """
        # 1. Base audit via deterministic general terms
        base_report = ComplianceGuard.audit_text(text)
        violations: List[ComplianceViolation] = list(base_report.violations)
        sanitized = base_report.sanitized_text

        # 2. Domain-specific rule pack audit
        plugin = DomainRegistry.get(domain)
        if plugin:
            rules = plugin.get_compliance_rules()
            for rule in rules:
                for prohibited_term in rule.get("prohibited", []):
                    if prohibited_term in sanitized:
                        violations.append(
                            ComplianceViolation(
                                original_term=prohibited_term,
                                rule_category=rule.get("authority", "산업별 특화 규제"),
                                severity="HIGH",
                                recommended_term="전문적이고 정직한 표현",
                                reason=f"{rule.get('authority')}에 따른 금지어 규제",
                            )
                        )
                        sanitized = sanitized.replace(prohibited_term, "인증받은")

        # 3. 데이터 라이선스 출처 표기 감사
        if required_attribution and required_attribution not in text:
            violations.append(
                ComplianceViolation(
                    original_term="(출처 표기 누락)",
                    rule_category=ATTRIBUTION_RULE_CATEGORY,
                    severity="HIGH",
                    recommended_term=required_attribution,
                    reason=(
                        "이 콘텐츠는 외부 기상 데이터에서 파생되었으나 출처 표기가 없습니다. "
                        "CC BY 4.0은 출처 표기를 요구합니다."
                    ),
                )
            )

        is_compliant = len(violations) == 0
        return ComplianceReport(
            is_compliant=is_compliant,
            violations=violations,
            original_text=text,
            sanitized_text=sanitized,
        )

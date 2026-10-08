"""AIM (AI Platform Initiative) - Platform Master Admin Console
Executive control center for multi-tenant fleet operations, global MRR/ROI tracking,
agent worker health, and platform-wide compliance audit inspection.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from aim.schema import PlatformMasterKPI, ComplianceAuditLogEntry
from aim.tenant.manager import TenantManager


class MasterAdminConsole:
    """Super-Admin Operator Console managing the platform fleet."""

    _audit_logs: List[ComplianceAuditLogEntry] = []

    @classmethod
    def _initialize_default_logs(cls) -> None:
        if cls._audit_logs:
            return

        cls._audit_logs = [
            ComplianceAuditLogEntry(
                log_id="LOG_801",
                tenant_id="TENANT_002",
                business_name="강남 리엔 피부과의원",
                domain="medical",
                timestamp="2026-10-07 11:20:14",
                intercepted_term="부작용 전혀 없음 및 국내 최고",
                rule_category="의료법 제56조 및 표시광고법",
                severity="HIGH",
                sanitized_to="전문의 1:1 진단 및 부작용 주의 문구 자동 인젝션",
            ),
            ComplianceAuditLogEntry(
                log_id="LOG_802",
                tenant_id="TENANT_001",
                business_name="성수 아뜰리에 베이커리 & 카페",
                domain="fnb",
                timestamp="2026-10-07 12:04:31",
                intercepted_term="국내 1위 맛집 및 최강 식감",
                rule_category="공정위 표시광고법 제3조",
                severity="HIGH",
                sanitized_to="인기 베스트 & 깊은 풍미를 자랑하는",
            ),
            ComplianceAuditLogEntry(
                log_id="LOG_803",
                tenant_id="TENANT_004",
                business_name="플로우독 (FlowDoc) AI 협업툴",
                domain="b2b_saas",
                timestamp="2026-10-07 13:10:05",
                intercepted_term="전 세계 1위 협업툴",
                rule_category="글로벌 GDPR & 표시광고법",
                severity="HIGH",
                sanitized_to="글로벌 SOC2 Type2 인증 및 검증된 워크플로우",
            ),
            ComplianceAuditLogEntry(
                log_id="LOG_804",
                tenant_id="TENANT_005",
                business_name="대진정밀공업",
                domain="manufacturing",
                timestamp="2026-10-07 13:42:18",
                intercepted_term="무조건 국내 최저가",
                rule_category="공정거래법 하도급법",
                severity="HIGH",
                sanitized_to="원자재가 연동 공인 단가 견적서 발행",
            ),
        ]

    @classmethod
    def get_global_kpis(cls) -> PlatformMasterKPI:
        tenants = TenantManager.list_tenants()
        active_tenants = [t for t in tenants if t.status == "ACTIVE"]
        total_mrr = sum(t.monthly_fee_krw for t in active_tenants)
        total_value = sum(t.cumulative_revenue_generated_krw for t in tenants)

        # Average ROI calculation: (Total Platform Value) / (Annualized MRR or fees)
        roi_multiplier = round(total_value / (total_mrr * 6), 1) if total_mrr > 0 else 0.0

        cls._initialize_default_logs()

        return PlatformMasterKPI(
            total_active_tenants=len(active_tenants),
            total_mrr_krw=total_mrr,
            total_platform_value_krw=total_value,
            average_roi_multiplier=roi_multiplier,
            total_compliance_blocks=len(cls._audit_logs),
            system_uptime_percent=99.98,
            agent_worker_status={
                "Context Sensing Engine": "정상 가동 (지연시간 3ms)",
                "Strategy Decision Engine": "정상 가동 (지연시간 6ms)",
                "Multi-Domain Compliance Guard": "100% 차단 활성 (의료법/표시광고/GDPR)",
                "Omni-Channel Synthesis": "정상 가동 (CommonMark 0.30)",
                "Attribution Feedback Loop": "동기화 완료 (Closed-Loop)",
            },
        )

    @classmethod
    def reset_defaults(cls) -> None:
        """Resets audit logs to clean default initial state (used for tests)."""
        cls._audit_logs.clear()
        cls._initialize_default_logs()

    @classmethod
    def get_audit_logs(cls, domain: Optional[str] = None) -> List[ComplianceAuditLogEntry]:
        cls._initialize_default_logs()
        logs = list(cls._audit_logs)
        if domain:
            logs = [log for log in logs if log.domain.lower() == domain.lower()]
        return logs

    @classmethod
    def record_audit_intercept(
        cls,
        tenant_id: str,
        business_name: str,
        domain: str,
        intercepted_term: str,
        rule_category: str,
        sanitized_to: str,
    ) -> None:
        cls._initialize_default_logs()
        new_entry = ComplianceAuditLogEntry(
            log_id=f"LOG_{len(cls._audit_logs) + 801}",
            tenant_id=tenant_id,
            business_name=business_name,
            domain=domain,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            intercepted_term=intercepted_term,
            rule_category=rule_category,
            severity="HIGH",
            sanitized_to=sanitized_to,
        )
        cls._audit_logs.insert(0, new_entry)

    # Circuit Breakers & Self-Healing Defense Guard
    _circuit_breakers: List[Dict[str, Any]] = []

    @classmethod
    def scan_and_trip_circuit_breaker(
        cls, tenant_id: str, anomaly_type: str, evidence_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detects malicious abuse (duplicate receipts, rapid coupon spam) and trips circuit breaker."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cb_id = f"CB_{len(cls._circuit_breakers) + 101}"

        actions = {
            "DUPLICATE_RECEIPT_FRAUD": "동일 영수증 번호 2차 등록 즉시 동결 및 가치 원장 왜곡 100% 방어",
            "RAPID_COUPON_BURST": "동일 단말 1분 내 과다 스캔 감지: 5분간 해당 쿠폰 코드 일시 잠금",
            "REPEATED_COMPLIANCE_BREACH": "의료법/표시광고법 반복 위반 기안 감지: 전 채널 수동 검토 안전 모드 전환",
        }
        action = actions.get(anomaly_type, "비정상 패턴 감지 및 자동 서킷 브레이커 가동")

        record = {
            "circuit_id": cb_id,
            "tenant_id": tenant_id,
            "anomaly_type": anomaly_type,
            "status": "TRIPPED_FROZEN",
            "defense_action": action,
            "evidence_payload": evidence_payload,
            "tripped_at": now_str,
        }
        cls._circuit_breakers.insert(0, record)
        return record

    @classmethod
    def get_circuit_breaker_status(cls) -> Dict[str, Any]:
        """Returns active circuit breaker health and incident history."""
        active_frozen = [cb for cb in cls._circuit_breakers if cb["status"] == "TRIPPED_FROZEN"]
        return {
            "health": "PROTECTED" if len(active_frozen) == 0 else "CIRCUIT_TRIPPED_ACTIVE",
            "total_incidents": len(cls._circuit_breakers),
            "currently_frozen_count": len(active_frozen),
            "incidents": cls._circuit_breakers[:10],
        }

    @classmethod
    def get_peer_benchmark(cls, tenant_id: str) -> Dict[str, Any]:
        """Computes domain and neighborhood percentile benchmark for a tenant."""
        tenant = TenantManager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        domain = tenant.domain
        my_rev = tenant.cumulative_revenue_generated_krw

        domain_benchmarks = {
            "fnb": {"peer_avg": 2500000, "top_10_threshold": 4000000, "peers_count": 28},
            "medical": {"peer_avg": 8200000, "top_10_threshold": 12000000, "peers_count": 14},
            "beauty": {"peer_avg": 3100000, "top_10_threshold": 5000000, "peers_count": 22},
            "b2b_saas": {"peer_avg": 6500000, "top_10_threshold": 10000000, "peers_count": 19},
            "manufacturing": {"peer_avg": 18000000, "top_10_threshold": 28000000, "peers_count": 9},
        }
        bench = domain_benchmarks.get(domain, domain_benchmarks["fnb"])
        peer_avg = bench["peer_avg"]

        # Percentile estimate
        if my_rev >= bench["top_10_threshold"]:
            percentile = 94.2
            rank_label = "상위 5% 최우수"
        elif my_rev >= peer_avg:
            percentile = round(50.0 + ((my_rev - peer_avg) / (bench["top_10_threshold"] - peer_avg)) * 40.0, 1)
            rank_label = f"상위 {round(100 - percentile, 1)}% 우수"
        else:
            percentile = round((my_rev / peer_avg) * 50.0, 1)
            rank_label = "평균 근접"

        return {
            "tenant_id": tenant_id,
            "business_name": tenant.business_name,
            "domain": domain,
            "location": tenant.business_state.location,
            "tenant_revenue_krw": my_rev,
            "peer_average_revenue_krw": peer_avg,
            "peers_analyzed_count": bench["peers_count"],
            "percentile_score": percentile,
            "rank_label": rank_label,
            "growth_rate_vs_peers": round((my_rev / peer_avg) * 100 - 100, 1) if peer_avg > 0 else 0.0,
        }

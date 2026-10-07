"""AIM (AI Platform Initiative) - Core Platform Architecture Package
"""

from aim.core.context_engine import ContextEngine
from aim.core.domain_registry import DomainRegistry
from aim.core.strategy_engine import StrategyEngine
from aim.core.synthesis_engine import ContentSynthesisEngine
from aim.core.compliance_engine import ComplianceEngine
from aim.core.platform import AIMPlatform

__all__ = [
    "ContextEngine",
    "DomainRegistry",
    "StrategyEngine",
    "ContentSynthesisEngine",
    "ComplianceEngine",
    "AIMPlatform",
]

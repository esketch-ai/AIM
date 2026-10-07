"""AIM (AI Platform Initiative) - Domain Plugin Architecture
Abstract Base Class for all business domain plugins.
Enables AIM to support ANY industry through modular plugin contracts.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from aim.schema import BusinessState, Context6D, StrategyObjective


class BaseDomainPlugin(ABC):
    """Abstract contract for business industry domains in the AIM platform."""

    @property
    @abstractmethod
    def domain_key(self) -> str:
        """Unique domain identifier (e.g. 'fnb', 'medical', 'beauty', 'b2b_saas', 'manufacturing')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable industry name in Korean."""
        pass

    @abstractmethod
    def evaluate_triggers(self, state: BusinessState, context: Context6D) -> StrategyObjective:
        """Evaluates operational state against 6D context to resolve strategy and financial projections."""
        pass

    @abstractmethod
    def get_compliance_rules(self) -> List[Dict[str, Any]]:
        """Returns domain-specific regulatory rules and required disclaimers."""
        pass

    @abstractmethod
    def get_channel_blueprint(
        self,
        channel_key: str,
        state: BusinessState,
        strategy: StrategyObjective,
        context: Context6D,
        tone: str = "DEFAULT",
    ) -> Dict[str, Any]:
        """Provides structured blueprints (headline concept, body points, cta concept, hashtags)
        for dynamic content synthesis without hardcoded templates.
        """
        pass

"""AIM (AI Platform Initiative) - Domain Registry
Central catalog for registering and discovering business domain plugins.
"""

from typing import Dict, List, Optional
from aim.domains.base import BaseDomainPlugin
from aim.domains.fnb import FnbDomainPlugin
from aim.domains.medical import MedicalDomainPlugin
from aim.domains.beauty import BeautyDomainPlugin
from aim.domains.b2b_saas import B2BSaaSDomainPlugin
from aim.domains.manufacturing import ManufacturingDomainPlugin


class DomainRegistry:
    """Registry maintaining all available business domain plugins."""

    _registry: Dict[str, BaseDomainPlugin] = {}

    @classmethod
    def register(cls, plugin: BaseDomainPlugin) -> None:
        cls._registry[plugin.domain_key] = plugin

    @classmethod
    def get(cls, domain_key: str) -> Optional[BaseDomainPlugin]:
        cls._ensure_defaults()
        return cls._registry.get(domain_key)

    @classmethod
    def list_domains(cls) -> List[Dict[str, str]]:
        cls._ensure_defaults()
        return [
            {"domain_key": k, "display_name": p.display_name}
            for k, p in cls._registry.items()
        ]

    @classmethod
    def _ensure_defaults(cls) -> None:
        if not cls._registry:
            cls.register(FnbDomainPlugin())
            cls.register(MedicalDomainPlugin())
            cls.register(BeautyDomainPlugin())
            cls.register(B2BSaaSDomainPlugin())
            cls.register(ManufacturingDomainPlugin())

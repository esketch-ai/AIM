"""AIM (AI Platform Initiative) - Domain Plugins Package
Provides pluggable domain models for F&B, Healthcare, Beauty, B2B SaaS, and Manufacturing.
"""

from aim.domains.base import BaseDomainPlugin
from aim.domains.fnb import FnbDomainPlugin
from aim.domains.medical import MedicalDomainPlugin
from aim.domains.beauty import BeautyDomainPlugin
from aim.domains.b2b_saas import B2BSaaSDomainPlugin
from aim.domains.manufacturing import ManufacturingDomainPlugin

__all__ = [
    "BaseDomainPlugin",
    "FnbDomainPlugin",
    "MedicalDomainPlugin",
    "BeautyDomainPlugin",
    "B2BSaaSDomainPlugin",
    "ManufacturingDomainPlugin",
]

"""Optional provider adapters.

Adapters deliberately use lazy imports so the MedSystem1 core remains dependency-light.
"""

from .openmed import OpenMedExtractionProvider
from .strands import StrandsDecisionProvider

__all__ = ["OpenMedExtractionProvider", "StrandsDecisionProvider"]

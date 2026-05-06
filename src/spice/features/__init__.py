"""Feature compilation and table execution."""

from .contracts import (
    CompiledFeatureContract,
    compile_feature_contract,
)
from .core import (
    CanonicalBlockSeries,
    FeaturePrerequisites,
    ResolvedFeatureTable,
)
from .registry import validate_feature_selection

__all__ = [
    "CanonicalBlockSeries",
    "CompiledFeatureContract",
    "FeaturePrerequisites",
    "ResolvedFeatureTable",
    "compile_feature_contract",
    "validate_feature_selection",
]

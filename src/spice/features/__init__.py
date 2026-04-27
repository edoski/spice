"""Feature compilation and table execution."""

from .contracts import (
    CompiledFeatureContract,
    compile_feature_contract,
)
from .core import (
    CanonicalBlockSeries,
    FeaturePrerequisites,
    ResolvedFeatureTable,
    build_feature_table,
)
from .registry import validate_feature_selection

__all__ = [
    "CanonicalBlockSeries",
    "CompiledFeatureContract",
    "FeaturePrerequisites",
    "ResolvedFeatureTable",
    "build_feature_table",
    "compile_feature_contract",
    "validate_feature_selection",
]

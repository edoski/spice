"""Family-aware Hamilton feature graph."""

from .contracts import (
    CompiledFeatureContract,
    compile_feature_contract,
)
from .engine import (
    CanonicalBlockSeries,
    FeatureSelection,
    ResolvedFeatureTable,
    build_feature_driver,
    build_feature_table,
    feature_graph_fingerprint,
    feature_node_map,
    make_feature_selection,
    resolve_feature_prerequisites,
    validate_feature_selection,
)
from .families import (
    FeatureFamilyConfig,
    FeatureFamilySpec,
    FeaturePrerequisites,
    coerce_feature_family_config,
    feature_family_spec,
)

__all__ = [
    "CanonicalBlockSeries",
    "CompiledFeatureContract",
    "FeatureFamilyConfig",
    "FeatureFamilySpec",
    "FeaturePrerequisites",
    "FeatureSelection",
    "ResolvedFeatureTable",
    "build_feature_driver",
    "build_feature_table",
    "compile_feature_contract",
    "coerce_feature_family_config",
    "feature_family_spec",
    "feature_graph_fingerprint",
    "feature_node_map",
    "make_feature_selection",
    "resolve_feature_prerequisites",
    "validate_feature_selection",
]

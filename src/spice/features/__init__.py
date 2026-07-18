"""Feature compilation and table execution."""

from .core import FeaturePrerequisites
from .registry import validate_feature_selection

__all__ = [
    "FeaturePrerequisites",
    "validate_feature_selection",
]

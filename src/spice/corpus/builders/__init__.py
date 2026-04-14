"""Dataset build seam for canonical acquisition outputs."""

from .evaluation import ensure_evaluation_dataset
from .history import ensure_history_dataset
from .shared import DatasetBuildOutcome, DatasetBuildResult

__all__ = [
    "DatasetBuildOutcome",
    "DatasetBuildResult",
    "ensure_evaluation_dataset",
    "ensure_history_dataset",
]

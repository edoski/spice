"""Direct native artifact evaluation."""

from .evaluate import evaluate
from .resolution import reduce_evaluation

__all__ = [
    "evaluate",
    "reduce_evaluation",
]

"""Direct native artifact evaluation."""

from .evaluate import EvaluationDeployment, evaluate
from .resolution import compare_rolling, reduce_evaluation

__all__ = [
    "EvaluationDeployment",
    "compare_rolling",
    "evaluate",
    "reduce_evaluation",
]

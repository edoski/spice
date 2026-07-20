"""Direct native artifact evaluation."""

from .evaluate import EvaluationDeployment, evaluate
from .resolution import ResolvedEvaluation, reduce_evaluation, resolve_evaluations

__all__ = [
    "EvaluationDeployment",
    "ResolvedEvaluation",
    "evaluate",
    "reduce_evaluation",
    "resolve_evaluations",
]

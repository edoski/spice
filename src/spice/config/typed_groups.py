"""Context-free typed loading for named config groups."""

from __future__ import annotations

from typing import cast

from ..evaluation import EvaluatorConfig
from ..modeling.families.base import ModelConfig
from .group_catalog import ConfigGroup, GroupSpec, group_spec
from .models import (
    ChainSpec,
    EvaluationsSpec,
    TrainingConfig,
)

CHAIN = cast(GroupSpec[ChainSpec], group_spec(ConfigGroup.CHAIN))
EVALUATOR = cast(GroupSpec[EvaluatorConfig], group_spec(ConfigGroup.EVALUATOR))
EVALUATIONS = cast(GroupSpec[EvaluationsSpec], group_spec(ConfigGroup.EVALUATIONS))
MODEL = cast(GroupSpec[ModelConfig[str]], group_spec(ConfigGroup.MODEL))
TRAINING = cast(GroupSpec[TrainingConfig], group_spec(ConfigGroup.TRAINING))

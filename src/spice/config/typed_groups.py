# pyright: strict

"""Context-free typed loading for named config groups."""

from __future__ import annotations

from typing import cast

from ..evaluation import EvaluatorConfig
from ..modeling.families.base import ModelConfig
from .group_catalog import ConfigGroup, GroupSpec, group_spec
from .models import (
    ChainSpec,
    EvaluationsSpec,
    ProblemSpec,
    SplitConfig,
    TrainingConfig,
)

CHAIN = cast(GroupSpec[ChainSpec], group_spec(ConfigGroup.CHAIN))
EVALUATOR = cast(GroupSpec[EvaluatorConfig], group_spec(ConfigGroup.EVALUATOR))
EVALUATIONS = cast(GroupSpec[EvaluationsSpec], group_spec(ConfigGroup.EVALUATIONS))
MODEL = cast(GroupSpec[ModelConfig[str]], group_spec(ConfigGroup.MODEL))
PROBLEM = cast(GroupSpec[ProblemSpec], group_spec(ConfigGroup.PROBLEM))
SPLIT = cast(GroupSpec[SplitConfig], group_spec(ConfigGroup.SPLIT))
TRAINING = cast(GroupSpec[TrainingConfig], group_spec(ConfigGroup.TRAINING))

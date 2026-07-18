"""Context-free typed loading for named config groups."""

from __future__ import annotations

from typing import cast

from ..evaluation import EvaluatorConfig
from .group_catalog import ConfigGroup, GroupSpec, group_spec
from .models import (
    ChainSpec,
    EvaluationsSpec,
)

CHAIN = cast(GroupSpec[ChainSpec], group_spec(ConfigGroup.CHAIN))
EVALUATOR = cast(GroupSpec[EvaluatorConfig], group_spec(ConfigGroup.EVALUATOR))
EVALUATIONS = cast(GroupSpec[EvaluationsSpec], group_spec(ConfigGroup.EVALUATIONS))

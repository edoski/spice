"""Full temporal replay evaluator."""

from __future__ import annotations

import numpy as np

from .config import FullTemporalReplayEvaluatorConfig
from .contracts import CompiledEvaluatorContract
from .temporal_replay_runner import (
    TemporalReplaySampleView,
    TemporalReplaySelection,
    compile_temporal_replay_evaluator_contract,
)


class FullTemporalReplayAdapter:
    def __init__(self, config: FullTemporalReplayEvaluatorConfig) -> None:
        self.config = config

    def selections(
        self,
        samples: TemporalReplaySampleView,
    ) -> list[TemporalReplaySelection]:
        return [
            TemporalReplaySelection(
                selected_positions=np.arange(samples.sample_count, dtype=np.int64),
                metadata={
                    "mode": self.config.id,
                    "sample_count": samples.sample_count,
                },
            )
        ]


def compile_full_temporal_replay_evaluator_contract(
    config: FullTemporalReplayEvaluatorConfig,
) -> CompiledEvaluatorContract:
    return compile_temporal_replay_evaluator_contract(
        evaluator_id=config.id,
        config=config,
        adapter=FullTemporalReplayAdapter(config),
    )

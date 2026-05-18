"""Corpus acquisition planning."""

from __future__ import annotations

from dataclasses import dataclass

from ..acquisition import BlockPullPlan, BlockSource, TimestampRange
from ..config.models import ChainRuntimeSpec, FeaturesConfig, ProblemSpec
from ..features import CompiledFeatureContract, compile_feature_contract
from ..temporal.contracts import CompiledProblemContract, compile_problem_contract
from .metadata import CorpusAcquisitionSourceRequirements

CORE_CORPUS_SOURCE_COLUMNS = frozenset({"block_number", "timestamp", "chain_id"})


@dataclass(frozen=True, slots=True)
class CorpusAcquisitionPlanningSpec:
    features: FeaturesConfig
    problem: ProblemSpec
    chain_runtime: ChainRuntimeSpec
    window_start_timestamp: int
    window_end_timestamp: int


@dataclass(frozen=True, slots=True)
class CorpusAcquisitionPlan:
    blocks_plan: BlockPullPlan
    requested_window_seconds: int


@dataclass(frozen=True, slots=True)
class CorpusAcquisitionPlanningContext:
    spec: CorpusAcquisitionPlanningSpec
    feature_contract: CompiledFeatureContract
    problem_contract: CompiledProblemContract

    @property
    def source_requirements(self) -> CorpusAcquisitionSourceRequirements:
        required_columns = frozenset(self.feature_contract.required_source_columns)
        return CorpusAcquisitionSourceRequirements(
            required_columns=CORE_CORPUS_SOURCE_COLUMNS | required_columns,
            optional_enrichments=self.feature_contract.acquisition_enrichments,
            temporal_unit="block",
            ordering_key="block_number",
            partition_key="chain_id",
        )

    async def initial_plan(self, block_source: BlockSource) -> CorpusAcquisitionPlan:
        window = TimestampRange(
            start=self.spec.window_start_timestamp,
            end=self.spec.window_end_timestamp,
        )
        return CorpusAcquisitionPlan(
            blocks_plan=await block_source.plan_window(window),
            requested_window_seconds=window.end - window.start,
        )


def build_corpus_acquisition_planning_context(
    spec: CorpusAcquisitionPlanningSpec,
) -> CorpusAcquisitionPlanningContext:
    feature_contract = compile_feature_contract(features=spec.features)
    problem_contract = compile_problem_contract(
        problem=spec.problem,
        feature_contract=feature_contract,
        chain_runtime=spec.chain_runtime,
    )
    return CorpusAcquisitionPlanningContext(
        spec=spec,
        feature_contract=feature_contract,
        problem_contract=problem_contract,
    )

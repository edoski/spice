from __future__ import annotations

import math
from typing import cast

from spice.acquisition import BlockPullPlan, BlockRange, TimestampRange
from spice.config import AcquireConfig, WorkflowTask
from spice.storage.catalog.index import list_dataset_records
from spice.storage.corpus import list_acquire_runs, load_corpus_manifest
from spice.storage.selectors import CorpusSelector
from spice.storage.workflow_root_materialization import materialize_acquire_roots
from spice.workflows.acquire import run as run_acquire
from tests.dataset_helpers import make_block_rows


def _load_config(load_workflow_config, tmp_path, acquire_override) -> AcquireConfig:
    return cast(
        AcquireConfig,
        load_workflow_config(
            WorkflowTask.ACQUIRE,
            workspace=tmp_path,
            override=acquire_override(),
        ),
    )


def _plan(config: AcquireConfig) -> BlockPullPlan:
    window = TimestampRange(
        start=config.corpus_window_start_timestamp,
        end=config.corpus_window_end_timestamp,
    )
    count = max(1, math.ceil((window.end - window.start) / 12))
    return BlockPullPlan(window=window, block_range=BlockRange(start=100, end=100 + count))


def test_acquire_workflow_writes_blocks_corpus_and_metadata(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    acquire_override,
) -> None:
    config = _load_config(load_workflow_config, tmp_path, acquire_override)
    roots = materialize_acquire_roots(config)
    plan = _plan(config)

    class FakeAcquireClient:
        def __init__(self, rpc_endpoint, chain, source_requirements) -> None:
            del rpc_endpoint
            assert source_requirements.temporal_unit == "block"
            self.chain = chain

        async def close(self) -> None:
            return None

        async def estimate_recent_block_interval(self, sample_size: int = 128) -> float:
            del sample_size
            return 12.0

        async def plan_window(self, window: TimestampRange) -> BlockPullPlan:
            assert window == plan.window
            return plan

        async def get_block_rows(self, start: int, end: int):
            return make_block_rows(
                end - start,
                start_block=start,
                start_timestamp=plan.window.start + (start - plan.block_range.start) * 12,
                chain_id=config.chain.runtime.chain_id,
                block_interval_seconds=12,
            )

    monkeypatch.setattr("spice.workflows.acquire.BlockRpcClient", FakeAcquireClient)

    run_acquire(config)

    manifest = load_corpus_manifest(roots.corpus.state_db_path)
    runs = list_acquire_runs(roots.corpus.state_db_path)
    assert roots.corpus.state_db_path.is_file()
    assert roots.corpus.blocks_dir.is_dir()
    assert manifest.blocks.coverage.rows == plan.block_range.count
    assert manifest.corpus.id == roots.corpus.corpus_id
    assert manifest.corpus.name == config.corpus.name
    assert runs[0].facts.requested_window_seconds == plan.window.end - plan.window.start

    records = list_dataset_records(
        roots.corpus.storage_root,
        selector=CorpusSelector(chain_name=config.chain.name, corpus_name=config.corpus.name),
    )
    assert [record.corpus_id for record in records] == [roots.corpus.corpus_id]

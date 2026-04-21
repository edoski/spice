"""Canonical block corpus acquisition workflow."""

from __future__ import annotations

import asyncio
import signal
import threading
import weakref
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.thread import _worker
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from ..acquisition.rpc import BlockRpcClient, RpcController, TimestampRange, evaluation_range
from ..config import AcquireConfig
from ..core.files import promote_paths_atomic, prune_empty_directories
from ..core.reporting import Reporter
from ..corpus.builders import ensure_evaluation_dataset, ensure_history_dataset
from ..corpus.io import load_block_frame
from ..corpus.metadata import (
    build_acquire_run_record,
    build_dataset_manifest,
    provider_metadata,
)
from ..corpus.summary import acquire_dry_run_fields, acquisition_result_fields
from ..features import CompiledFeatureContract, compile_feature_contract
from ..storage.catalog import upsert_dataset_record
from ..storage.corpus import write_dataset_state
from ..storage.layout import resolve_workflow_paths
from ..temporal.contracts import CompiledProblemContract, compile_problem_contract
from ._shared import managed_workflow


def _workflow_facts(config: AcquireConfig) -> list[tuple[str, str]]:
    return [
        ("dataset", config.dataset.name),
        ("chain", config.chain.name),
        ("problem", config.problem.id),
        ("provider", config.provider.name),
    ]


def _count_valid_history_samples(
    *,
    history_dir: Path,
    feature_contract: CompiledFeatureContract,
    contract: CompiledProblemContract,
) -> int:
    blocks = load_block_frame(history_dir).sort("block_number")
    feature_table = feature_contract.build_table(blocks)
    return contract.count_valid_capability_samples(feature_table)


class _DaemonThreadPoolExecutor(ThreadPoolExecutor):
    """Default executor variant that doesn't block interpreter shutdown on SIGINT."""

    def _adjust_thread_count(self) -> None:
        if self._idle_semaphore.acquire(timeout=0):
            return

        def weakref_cb(_, q=self._work_queue):
            cast(Any, q).put(None)

        num_threads = len(self._threads)
        if num_threads >= self._max_workers:
            return
        thread_name = f"{self._thread_name_prefix or self}_{num_threads}"
        thread = threading.Thread(
            name=thread_name,
            target=_worker,
            args=(
                weakref.ref(self, weakref_cb),
                self._work_queue,
                cast(Any, self)._initializer,
                cast(Any, self)._initargs,
            ),
        )
        thread.daemon = True
        thread.start()
        cast(set[threading.Thread], self._threads).add(thread)
        # Skip concurrent.futures' global exit registry so a cancelled acquire
        # doesn't hang in interpreter shutdown waiting for RPC worker threads.


def _run_async_interruptibly(coro: Coroutine[Any, Any, None]) -> None:
    loop = asyncio.new_event_loop()
    executor = _DaemonThreadPoolExecutor(thread_name_prefix="spice-asyncio")
    loop.set_default_executor(executor)
    task = loop.create_task(coro)
    interrupted = False
    previous_sigint = None

    def _handle_sigint(signum, frame) -> None:
        del signum, frame
        nonlocal interrupted
        interrupted = True
        if not task.done():
            loop.call_soon_threadsafe(task.cancel)

    try:
        with suppress(ValueError):
            previous_sigint = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, _handle_sigint)
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            interrupted = True
        except KeyboardInterrupt:
            interrupted = True
            if not task.done():
                task.cancel()
                with suppress(BaseException):
                    loop.run_until_complete(task)
    finally:
        if previous_sigint is not None:
            with suppress(ValueError):
                signal.signal(signal.SIGINT, previous_sigint)
        pending = [
            pending_task for pending_task in asyncio.all_tasks(loop) if not pending_task.done()
        ]
        for pending_task in pending:
            pending_task.cancel()
        if pending and not interrupted:
            with suppress(BaseException):
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        with suppress(BaseException):
            loop.run_until_complete(loop.shutdown_asyncgens())
        executor.shutdown(wait=False, cancel_futures=True)
        asyncio.set_event_loop(None)
        loop.close()


def run(config: AcquireConfig, *, reporter: Reporter | None = None) -> None:
    try:
        _run_async_interruptibly(_run_async(config, reporter=reporter))
    except KeyboardInterrupt:
        return None


async def _run_async(config: AcquireConfig, *, reporter: Reporter | None = None) -> None:
    paths = resolve_workflow_paths(config)
    history_dir = paths.history_dir
    evaluation_dir = paths.evaluation_dir
    state_db_path = paths.corpus_state_db
    rpc_controller = RpcController.from_config(config.acquisition)
    feature_contract = compile_feature_contract(feature_set=config.feature_set)
    contract = compile_problem_contract(
        problem=config.problem,
        feature_contract=feature_contract,
        chain_runtime=config.chain.runtime,
    )
    evaluation_window = evaluation_range(
        config.evaluation_window_start_timestamp,
        config.evaluation_window_end_timestamp,
    )

    with managed_workflow(reporter=reporter) as active_reporter:
        active_reporter.header("acquire", _workflow_facts(config))

        block_client = BlockRpcClient(config.provider, config.chain)
        try:
            evaluation_plan = await block_client.plan_window(
                evaluation_window,
                chunk_size=config.acquisition.chunk_size,
            )
            estimated_block_interval_seconds = await block_client.estimate_recent_block_interval()
            history_window_seconds = contract.initial_history_window_seconds(
                estimated_block_interval_seconds,
            )
            history_start_timestamp = max(
                0,
                config.history_window_end_timestamp - history_window_seconds,
            )
            history_plan = await block_client.plan_window(
                TimestampRange(
                    start=history_start_timestamp,
                    end=config.history_window_end_timestamp,
                ),
                chunk_size=config.acquisition.chunk_size,
            )

            if config.acquisition.dry_run:
                active_reporter.result(
                    "acquire",
                    acquire_dry_run_fields(
                        config,
                        contract=contract,
                        history_window_seconds=history_window_seconds,
                        history_plan=history_plan,
                        evaluation_plan=evaluation_plan,
                    ),
                    status="dry_run",
                )
                return

            current_provider = provider_metadata(config)
            paths.corpus_root.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(
                dir=paths.corpus_root.parent,
                prefix=f".{paths.corpus_id}.acquire.",
            ) as temp_root_name:
                temp_root = Path(temp_root_name)
                history_source_dir = history_dir
                history_iteration = 0
                while True:
                    history_work_dir = temp_root / f"history-pass-{history_iteration:02d}"
                    history_result = await ensure_history_dataset(
                        config=config,
                        block_client=block_client,
                        output_dir=history_source_dir,
                        working_dir=history_work_dir,
                        history_plan=history_plan,
                        rpc_controller=rpc_controller,
                        status=active_reporter.milestone,
                    )
                    valid_anchor_samples = _count_valid_history_samples(
                        history_dir=history_result.path,
                        feature_contract=feature_contract,
                        contract=contract,
                    )
                    if valid_anchor_samples >= contract.sample_count:
                        break
                    active_reporter.milestone(
                        "history extending window "
                        f"anchors={valid_anchor_samples}/{contract.sample_count}"
                    )
                    history_source_dir = history_result.path
                    history_iteration += 1
                    history_window_seconds *= 2
                    history_start_timestamp = max(
                        0,
                        config.history_window_end_timestamp - history_window_seconds,
                    )
                    history_plan = await block_client.plan_window(
                        TimestampRange(
                            start=history_start_timestamp,
                            end=config.history_window_end_timestamp,
                        ),
                        chunk_size=config.acquisition.chunk_size,
                    )

                evaluation_result = await ensure_evaluation_dataset(
                    config=config,
                    block_client=block_client,
                    output_dir=evaluation_dir,
                    working_dir=temp_root,
                    evaluation_plan=evaluation_plan,
                    rpc_controller=rpc_controller,
                    status=active_reporter.milestone,
                )
                manifest = build_dataset_manifest(
                    config=config,
                    contract=contract,
                    feature_contract=feature_contract,
                    history_request_start_timestamp=history_plan.window.start,
                    history_request_end_timestamp=history_plan.window.end,
                    evaluation_request_start_timestamp=evaluation_window.start,
                    evaluation_request_end_timestamp=evaluation_window.end,
                    history_validation=history_result.validation,
                    evaluation_validation=evaluation_result.validation,
                )
                acquire_run = build_acquire_run_record(
                    config=config,
                    provider=current_provider,
                    contract=contract,
                    acquisition_runtime=rpc_controller.snapshot(),
                    acquired_history_window_seconds=history_window_seconds,
                    valid_anchor_samples=valid_anchor_samples,
                )
                temp_state_db = temp_root / ".spice" / "state.sqlite"
                write_dataset_state(
                    temp_state_db,
                    manifest=manifest,
                    acquire_run=acquire_run,
                )
                promotions: list[tuple[Path, Path]] = []
                if history_result.promote_dir is not None:
                    promotions.append((history_dir, history_result.promote_dir))
                if evaluation_result.promote_dir is not None:
                    promotions.append((evaluation_dir, evaluation_result.promote_dir))
                promotions.append((state_db_path, temp_state_db))
                promote_paths_atomic(promotions)
                upsert_dataset_record(
                    paths.catalog_db,
                    dataset_id=paths.corpus_id,
                    dataset_name=config.dataset.name,
                    chain_name=config.chain.name,
                    root_path=paths.corpus_root,
                    state_db_path=state_db_path,
                )
            active_reporter.result(
                "acquire",
                acquisition_result_fields(
                    history_outcome=history_result.outcome,
                    history_row_count=history_result.validation.row_count,
                    evaluation_outcome=evaluation_result.outcome,
                    evaluation_row_count=evaluation_result.validation.row_count,
                ),
            )
        except (KeyboardInterrupt, asyncio.CancelledError):
            prune_empty_directories(
                paths.corpus_root,
                stop_at=paths.corpus_root.parent.parent,
            )
            active_reporter.milestone(
                "acquire cancelled; partial download removed",
                level="warning",
            )
            raise
        except Exception:
            active_reporter.milestone(
                "acquire failed; partial download removed",
                level="warning",
            )
            raise
        finally:
            await block_client.close()

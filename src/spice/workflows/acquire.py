"""Canonical block corpus acquisition workflow."""

from __future__ import annotations

import asyncio

from ..acquisition.rpc import BlockRpcClient
from ..config.models import AcquireConfig
from ..core.async_runtime import run_interruptibly
from ..core.reporting import Reporter
from ..corpus.assembly import assemble_corpus
from .preparation import prepare_acquire
from .reporting import (
    acquire_workflow_facts,
    report_acquire_result,
    report_acquire_staging_warning,
)


def run(config: AcquireConfig, *, reporter: Reporter | None = None) -> None:
    try:
        run_interruptibly(_run_async(config, reporter=reporter))
    except KeyboardInterrupt:
        return None


async def _run_async(config: AcquireConfig, *, reporter: Reporter | None = None) -> None:
    active_reporter = reporter or Reporter()
    active_reporter.header("acquire", acquire_workflow_facts(config))
    prepared = prepare_acquire(config)
    assembly_request = prepared.assembly_request
    block_client = BlockRpcClient(
        config.rpc_endpoint,
        config.chain,
        assembly_request.source_requirements,
    )
    try:
        result = await assemble_corpus(
            assembly_request,
            block_client,
            status=active_reporter.milestone,
        )
        report_acquire_result(active_reporter, result=result)
    except (KeyboardInterrupt, asyncio.CancelledError):
        report_acquire_staging_warning(active_reporter, reason="cancelled")
        raise
    except Exception:
        report_acquire_staging_warning(active_reporter, reason="failed")
        raise
    finally:
        await block_client.close()

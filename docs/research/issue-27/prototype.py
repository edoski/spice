#!/usr/bin/env python3
"""Interactive disposable driver for the issue-27 logic prototype."""

from __future__ import annotations

import argparse
import asyncio
import errno
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import polars as pl
from prototype_logic import (
    ContractError,
    CorpusDefinition,
    ReacquireRequired,
    Regime,
    SyntheticProvider,
    acquire_missing,
    as_jsonable,
    build_candidate,
    import_existing_payload,
    inspect_stage,
    publish_no_replace,
    write_payload_fixture,
)

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"


def definition(*, last_block: int = 107) -> CorpusDefinition:
    return CorpusDefinition(
        chain_id=1,
        regime=Regime(name="synthetic-modern", start_block=100),
        first_block=100,
        last_block=last_block,
    )


async def happy(root: Path) -> dict[str, object]:
    spec = definition(last_block=105)
    first_provider = SyntheticProvider(chain_id=1, last_available=108, finalized_number=108)
    second_provider = SyntheticProvider(chain_id=1, last_available=108, finalized_number=108)
    first_stage = root / "work-a" / "blocks"
    second_stage = root / "work-b" / "blocks"
    first_pull = await acquire_missing(
        spec,
        first_stage,
        first_provider,
        chunk_rows=2,
        concurrency=3,
    )
    second_pull = await acquire_missing(
        spec,
        second_stage,
        second_provider,
        chunk_rows=3,
        concurrency=3,
    )
    candidate = await build_candidate(
        spec,
        first_stage,
        root / "corpora",
        first_provider,
    )
    second_candidate = await build_candidate(
        spec,
        second_stage,
        root / "corpora",
        second_provider,
    )
    if candidate.corpus_id != second_candidate.corpus_id:
        raise ContractError("ephemeral stage chunk tuning changed canonical identity")
    final_columns = tuple(
        pl.read_parquet(sorted((candidate.path / "blocks").glob("*.parquet"))[0]).columns
    )
    if "definition_sha256" in final_columns:
        raise ContractError("stage-only definition binding leaked into final payload")
    first = publish_no_replace(candidate, root / "corpora")
    second = publish_no_replace(second_candidate, root / "corpora")
    return {
        "contract": "complete stage -> fixed anchor proof -> content id -> no-replace",
        "pulls_with_runtime_chunk_rows_2_and_3": [first_pull, second_pull],
        "corpus_id": candidate.corpus_id,
        "chunk_tuning_changes_identity": candidate.corpus_id != second_candidate.corpus_id,
        "definition_binding_in_final_payload": "definition_sha256" in final_columns,
        "first_publication": first.outcome,
        "exact_repeat": second.outcome,
        "persisted_runtime_facts": [],
    }


async def interrupted_resume(root: Path) -> dict[str, object]:
    spec = definition()
    stage = root / "work" / "blocks"
    failed_provider = SyntheticProvider(
        chain_id=1,
        last_available=110,
        finalized_number=110,
        terminal_fail_blocks={104},
    )
    failure = ""
    try:
        await acquire_missing(spec, stage, failed_provider, chunk_rows=2, concurrency=3)
    except ContractError as exc:
        failure = str(exc)
    prefix = inspect_stage(stage, spec)

    mismatches = {
        "changed_regime_name": CorpusDefinition(
            chain_id=spec.chain_id,
            regime=Regime(name="synthetic-other", start_block=spec.regime.start_block),
            first_block=spec.first_block,
            last_block=spec.last_block,
        ),
        "changed_last_block": definition(last_block=108),
    }
    mismatch_errors: dict[str, str] = {}
    mismatch_provider_calls: dict[str, int] = {}
    for label, changed_spec in mismatches.items():
        mismatch_provider = SyntheticProvider(
            chain_id=1,
            last_available=110,
            finalized_number=110,
        )
        try:
            await acquire_missing(
                changed_spec,
                stage,
                mismatch_provider,
                chunk_rows=2,
                concurrency=3,
            )
        except ContractError as exc:
            mismatch_errors[label] = str(exc)
        else:
            raise ContractError(f"{label} unexpectedly reused the private stage")
        mismatch_provider_calls[label] = sum(mismatch_provider.calls.values())
        if mismatch_provider_calls[label] != 0:
            raise ContractError(f"{label} reached the provider before stage rejection")

    resumed_provider = SyntheticProvider(chain_id=1, last_available=110, finalized_number=110)
    resumed = await acquire_missing(spec, stage, resumed_provider, chunk_rows=2, concurrency=3)
    final = inspect_stage(stage, spec)
    return {
        "terminal_error": failure,
        "cancelled_siblings": failed_provider.cancelled_calls,
        "durable_prefix_after_failure": prefix,
        "definition_mismatch_errors": mismatch_errors,
        "provider_calls_before_definition_rejection": mismatch_provider_calls,
        "resume_observation": resumed,
        "final_stage": final,
        "resume_marker_files": [],
        "checkpoint": "validated immutable Parquet prefix itself",
    }


async def invalid_partial(root: Path) -> dict[str, object]:
    spec = definition(last_block=103)
    provider = SyntheticProvider(chain_id=1, last_available=105, finalized_number=105)
    stage = root / "work" / "blocks"
    await acquire_missing(spec, stage, provider, chunk_rows=2, concurrency=2)
    second = sorted(stage.glob("*.parquet"))[1]
    frame = pl.read_parquet(second)
    frame = frame.with_columns(pl.lit("0" * 64).alias("parent_hash"))
    frame.write_parquet(second)
    failure = ""
    try:
        inspect_stage(stage, spec)
    except ContractError as exc:
        failure = str(exc)
    return {
        "validation_error": failure,
        "stage_preserved": stage.exists(),
        "next_action": "new disposable stage and reacquire; no truncate/repair",
    }


async def finality_mismatch(root: Path) -> dict[str, object]:
    spec = definition(last_block=103)
    provider = SyntheticProvider(
        chain_id=1,
        last_available=105,
        finalized_number=105,
        anchor_reread_mismatch=True,
    )
    stage = root / "work" / "blocks"
    await acquire_missing(spec, stage, provider, chunk_rows=2, concurrency=2)
    failure = ""
    try:
        await build_candidate(spec, stage, root / "corpora", provider)
    except ContractError as exc:
        failure = str(exc)
    visible = list((root / "corpora").glob("[0-9a-f]*")) if (root / "corpora").exists() else []
    return {
        "validation_error": failure,
        "canonical_packages": [path.name for path in visible],
        "result": "failure leaves no final package",
    }


async def conflict(root: Path) -> dict[str, object]:
    spec = definition(last_block=103)
    provider = SyntheticProvider(chain_id=1, last_available=105, finalized_number=105)
    stage = root / "work" / "blocks"
    await acquire_missing(spec, stage, provider, chunk_rows=2, concurrency=2)
    first_candidate = await build_candidate(spec, stage, root / "corpora", provider)
    publication = publish_no_replace(first_candidate, root / "corpora")
    payload_file = sorted((publication.canonical_path / "blocks").glob("*.parquet"))[0]
    with payload_file.open("ab") as handle:
        handle.write(b"conflict")
    second_candidate = await build_candidate(spec, stage, root / "corpora", provider)
    failure = ""
    try:
        publish_no_replace(second_candidate, root / "corpora")
    except ContractError as exc:
        failure = str(exc)

    ambiguous_spec = definition(last_block=104)
    ambiguous_provider = SyntheticProvider(
        chain_id=1,
        last_available=106,
        finalized_number=106,
    )
    ambiguous_stage = root / "ambiguous-work" / "blocks"
    await acquire_missing(
        ambiguous_spec,
        ambiguous_stage,
        ambiguous_provider,
        chunk_rows=2,
        concurrency=2,
    )
    ambiguous_candidate = await build_candidate(
        ambiguous_spec,
        ambiguous_stage,
        root / "ambiguous-corpora",
        ambiguous_provider,
    )

    def lose_success_reply(source: Path, destination: Path) -> None:
        os.rename(source, destination)
        raise OSError(errno.EIO, "simulated lost rename success reply", destination)

    ambiguous_failure = ""
    with patch("prototype_logic._exclusive_rename", side_effect=lose_success_reply):
        try:
            publish_no_replace(ambiguous_candidate, root / "ambiguous-corpora")
        except ContractError as exc:
            ambiguous_failure = str(exc)
    ambiguous_canonical = (
        root / "ambiguous-corpora" / ambiguous_candidate.corpus_id
    )
    if not ambiguous_failure or not ambiguous_canonical.exists():
        raise ContractError("lost rename success was not preserved as ambiguous")
    return {
        "existing_same_id_tampered": True,
        "conflict": failure,
        "canonical_preserved": publication.canonical_path.exists(),
        "candidate_preserved": second_candidate.path.exists(),
        "ambiguous_rename_error": ambiguous_failure,
        "ambiguous_visible_canonical_preserved": ambiguous_canonical.exists(),
    }


async def existing_parquet(root: Path) -> dict[str, object]:
    spec = definition(last_block=103)
    provider = SyntheticProvider(chain_id=1, last_available=105, finalized_number=105)
    existing = root / "existing" / "blocks"
    write_payload_fixture(existing, spec, provider, chunk_rows=2)
    stage = root / "fresh" / "blocks"
    await import_existing_payload(existing, spec, stage, provider)
    candidate = await build_candidate(spec, stage, root / "corpora", provider)

    bad_existing = root / "bad-existing" / "blocks"
    shutil.copytree(existing, bad_existing)
    bad_file = sorted(bad_existing.glob("*.parquet"))[0]
    bad_frame = pl.read_parquet(bad_file).with_columns(
        (pl.col("timestamp") + 1).alias("timestamp")
    )
    bad_frame.write_parquet(bad_file)
    failure = ""
    try:
        await import_existing_payload(
            bad_existing,
            spec,
            root / "bad-fresh" / "blocks",
            provider,
        )
    except ReacquireRequired as exc:
        failure = str(exc)

    mismatched_spec = CorpusDefinition(
        chain_id=spec.chain_id,
        regime=Regime(name="synthetic-other", start_block=spec.regime.start_block),
        first_block=spec.first_block,
        last_block=spec.last_block,
    )
    mismatched_target = root / "mismatched-target" / "blocks"
    target_provider = SyntheticProvider(
        chain_id=1,
        last_available=105,
        finalized_number=105,
    )
    await acquire_missing(
        mismatched_spec,
        mismatched_target,
        target_provider,
        chunk_rows=2,
        concurrency=2,
    )
    target_bytes_before = {
        path.name: path.read_bytes() for path in sorted(mismatched_target.glob("*.parquet"))
    }
    preflight_provider = SyntheticProvider(
        chain_id=1,
        last_available=105,
        finalized_number=105,
    )
    target_failure = ""
    try:
        await import_existing_payload(
            existing,
            spec,
            mismatched_target,
            preflight_provider,
        )
    except ReacquireRequired as exc:
        target_failure = str(exc)
    target_bytes_after = {
        path.name: path.read_bytes() for path in sorted(mismatched_target.glob("*.parquet"))
    }
    if sum(preflight_provider.calls.values()) != 0 or target_bytes_after != target_bytes_before:
        raise ContractError("mismatched import target was touched before rejection")
    return {
        "valid_existing_result": "freshly validated and assigned new-layout content identity",
        "corpus_id": candidate.corpus_id,
        "source_rows_reread": sum(provider.calls.values()),
        "invalid_existing_result": failure,
        "mismatched_target_result": target_failure,
        "provider_calls_before_target_rejection": sum(preflight_provider.calls.values()),
        "mismatched_target_unchanged": target_bytes_after == target_bytes_before,
    }


SCENARIOS = {
    "happy": happy,
    "resume": interrupted_resume,
    "invalid": invalid_partial,
    "finality": finality_mismatch,
    "conflict": conflict,
    "existing": existing_parquet,
}


async def run(name: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"issue-27-{name}-") as temporary:
        return await SCENARIOS[name](Path(temporary))


async def run_all() -> dict[str, object]:
    return {name: await run(name) for name in SCENARIOS}


def render(state: object) -> None:
    print(f"{BOLD}Current state{RESET}")
    print(json.dumps(as_jsonable(state), indent=2, sort_keys=True))
    print()


def interactive() -> None:
    state: object = {"question": "Does the exact-root state model stay lean under failure?"}
    while True:
        print("\x1b[2J\x1b[H", end="")
        render(state)
        print(f"{BOLD}[h]{RESET} {DIM}happy/no-op{RESET}  ", end="")
        print(f"{BOLD}[r]{RESET} {DIM}interrupt/resume{RESET}  ", end="")
        print(f"{BOLD}[i]{RESET} {DIM}invalid stage{RESET}")
        print(f"{BOLD}[f]{RESET} {DIM}finality mismatch{RESET}  ", end="")
        print(f"{BOLD}[c]{RESET} {DIM}same-id conflict{RESET}  ", end="")
        print(f"{BOLD}[e]{RESET} {DIM}existing Parquet{RESET}")
        print(f"{BOLD}[a]{RESET} {DIM}all{RESET}  {BOLD}[q]{RESET} {DIM}quit{RESET}")
        choice = input("> ").strip().lower()
        names = {
            "h": "happy",
            "r": "resume",
            "i": "invalid",
            "f": "finality",
            "c": "conflict",
            "e": "existing",
        }
        if choice == "q":
            return
        try:
            state = asyncio.run(run_all() if choice == "a" else run(names[choice]))
        except KeyError:
            state = {"error": f"unknown command: {choice}"}
        except Exception as exc:
            state = {"error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--scenario", choices=tuple(SCENARIOS))
    args = parser.parse_args()
    if args.all:
        render(asyncio.run(run_all()))
    elif args.scenario:
        render(asyncio.run(run(args.scenario)))
    else:
        interactive()


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
from shutil import copy2

from spice.acquisition import BlockPullPlan, BlockRange, TimestampRange
from spice.config.resolution import resolve_workflow_config
from spice.config.selections import AcquireWorkflowSelection
from spice.core.files import remove_path
from spice.corpus.io import iter_block_files
from spice.corpus.metadata import (
    AcquireRunFacts,
    CorpusManifest,
    build_dataset_manifest,
)
from spice.corpus.split_materialization._parquet_io import validate_block_dataset
from spice.storage.corpus import list_acquire_runs, load_corpus_manifest, write_corpus_state
from spice.storage.workflow_root_materialization import produced_corpus_id


ROOT = Path(__file__).resolve().parents[2]
CHAIN = "ethereum"
OLD_CORPUS_ID = "cor_2edb8f7b84a4edf95e2b"
SUFFIX_CORPUS_ID = "cor_ed5ef1b0eee8dfc8d702"
MERGED_CORPUS_NAME = "ethereum_pectra_to_2026_06_20"


def corpus_root(corpus_id: str) -> Path:
    return ROOT / "outputs" / "corpora" / CHAIN / corpus_id


def load_clean_manifest(corpus_id: str) -> CorpusManifest:
    root = corpus_root(corpus_id)
    manifest = load_corpus_manifest(root / ".spice" / "state.sqlite")
    if manifest.blocks.validation.status != "clean":
        raise RuntimeError(f"Corpus {corpus_id} is not clean: {manifest.blocks.validation}")
    return manifest


def assert_adjacent(old: CorpusManifest, suffix: CorpusManifest) -> None:
    old_last = old.blocks.coverage.last_block
    suffix_first = suffix.blocks.coverage.first_block
    if old_last is None or suffix_first is None:
        raise RuntimeError("Missing block coverage in source corpora")
    if suffix_first != old_last + 1:
        raise RuntimeError(
            "Source corpora are not adjacent: "
            f"old last={old_last}, suffix first={suffix_first}"
        )


def copy_block_files(destination: Path) -> int:
    remove_path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    count = 0
    for source_root in (corpus_root(OLD_CORPUS_ID), corpus_root(SUFFIX_CORPUS_ID)):
        for source_file in iter_block_files(source_root / "blocks"):
            target = destination / source_file.name
            if target.exists():
                raise RuntimeError(f"Duplicate target block file: {target}")
            copy2(source_file, target)
            count += 1
    return count


def main() -> None:
    old = load_clean_manifest(OLD_CORPUS_ID)
    suffix = load_clean_manifest(SUFFIX_CORPUS_ID)
    assert_adjacent(old, suffix)

    config = resolve_workflow_config(
        AcquireWorkflowSelection(
            surface="current_row_fee_dynamics",
            chain=CHAIN,
            corpus=MERGED_CORPUS_NAME,
        )
    )
    merged_corpus_id = produced_corpus_id(config)
    merged_root = corpus_root(merged_corpus_id)
    blocks_dir = merged_root / "blocks"
    state_db = merged_root / ".spice" / "state.sqlite"

    file_count = copy_block_files(blocks_dir)
    validation = validate_block_dataset(
        blocks_dir,
        expected_chain_id=config.chain.runtime.chain_id,
        required_columns=old.source_requirements.required_columns,
    )
    if validation.status != "clean":
        raise RuntimeError(f"Merged corpus validation failed: {validation}")

    plan = BlockPullPlan(
        window=TimestampRange(
            start=config.corpus_window_start_timestamp,
            end=config.corpus_window_end_timestamp,
        ),
        block_range=BlockRange(
            start=old.blocks.request.start_block,
            end=suffix.blocks.request.end_block,
        ),
    )
    manifest = build_dataset_manifest(
        config=config,
        corpus_id=merged_corpus_id,
        blocks_plan=plan,
        blocks_validation=validation,
        blocks_outcome="extended",
        blocks_file_count=file_count,
        source_requirements=old.source_requirements,
    )

    suffix_runs = list_acquire_runs(corpus_root(SUFFIX_CORPUS_ID) / ".spice" / "state.sqlite")
    if not suffix_runs:
        raise RuntimeError("Suffix corpus has no acquire run record")
    acquire_run = suffix_runs[0].model_copy(
        update={
            "facts": AcquireRunFacts(
                requested_window_seconds=config.corpus_window_end_timestamp
                - config.corpus_window_start_timestamp
            )
        }
    )
    write_corpus_state(state_db, manifest=manifest, acquire_run=acquire_run)
    print(
        "merged",
        f"corpus_id={merged_corpus_id}",
        f"blocks={validation.row_count}",
        f"files={file_count}",
        f"range={validation.first_block_number}-{validation.last_block_number}",
    )


if __name__ == "__main__":
    main()

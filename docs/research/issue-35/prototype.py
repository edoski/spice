"""Thin terminal driver for the Issue 35 disposable prototype."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import polars as pl
from prototype_logic import (
    OBSERVATION_SCHEMA,
    AuthorityError,
    EvaluationInput,
    exact_collection_paths,
    reduce_evaluations,
)

EVALUATION_IDS = (
    "10000000-0000-4000-8000-000000000001",
    "10000000-0000-4000-8000-000000000002",
)
ARTIFACT_ID = "20000000-0000-4000-8000-000000000001"
CORPUS_ID = "30000000-0000-4000-8000-000000000001"


def _observations(offset: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "origin_block": pl.Series([100 + offset, 101 + offset, 102 + offset], dtype=pl.Int64),
            "origin_timestamp": pl.Series(
                [1_700_000_000 + offset, 1_700_000_012 + offset, 1_700_000_024 + offset],
                dtype=pl.Int64,
            ),
            "selected_action_k": pl.Series([0, 1, 2], dtype=pl.Int64),
            "earliest_hindsight_action_k": pl.Series([0, 2, 2], dtype=pl.Int64),
            "classification_loss_contribution": pl.Series([0.1, 0.8, 0.2], dtype=pl.Float64),
            "predicted_hindsight_minimum_base_fee_z": pl.Series([-0.2, 0.1, 0.3], dtype=pl.Float32),
            "previous_closed_parent_base_fee_per_gas": pl.Series([110, 100, 120], dtype=pl.Int64),
            "closed_parent_base_fee_per_gas": pl.Series([100, 120, 130], dtype=pl.Int64),
            "immediate_k0_base_fee_per_gas": pl.Series([100, 120, 130], dtype=pl.Int64),
            "selected_target_base_fee_per_gas": pl.Series([100, 105, 90], dtype=pl.Int64),
            "hindsight_minimum_base_fee_per_gas": pl.Series([100, 90, 90], dtype=pl.Int64),
            "selected_action_wait_seconds": pl.Series([0, 12, 24], dtype=pl.Int64),
            "full_horizon_elapsed_seconds": pl.Series([24, 24, 24], dtype=pl.Int64),
        },
        schema=OBSERVATION_SCHEMA,
    )


def _make_fixture(root: Path) -> tuple[EvaluationInput, ...]:
    checkpoint_path = root / "artifacts" / f"{ARTIFACT_ID}.ckpt"
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "artifact_id": ARTIFACT_ID,
                "action_width": 3,
                "target_log_mean": 4.6,
                "target_log_std": 0.25,
            }
        ),
        encoding="utf-8",
    )
    inputs = []
    for ordinal, evaluation_id in enumerate(EVALUATION_IDS):
        evaluation_dir = root / "evaluations" / evaluation_id
        evaluation_dir.mkdir(parents=True)
        request = {
            "workflow": "evaluate",
            "evaluation_id": evaluation_id,
            "artifact_id": ARTIFACT_ID,
            "corpus_id": CORPUS_ID,
            "window": {
                "prototype_role": "testing",
                "prototype_start_block": 100 + ordinal * 10,
                "prototype_end_block_exclusive": 103 + ordinal * 10,
            },
        }
        (evaluation_dir / "evaluation.json").write_text(json.dumps(request), encoding="utf-8")
        _observations(ordinal * 10).write_parquet(evaluation_dir / "observations.parquet")
        inputs.append(EvaluationInput(evaluation_dir, checkpoint_path))
    return tuple(inputs)


def _collection_report(inputs: tuple[EvaluationInput, ...]) -> None:
    sealed = exact_collection_paths(inputs)
    print("COLLECTION")
    print("evaluation pairs, caller order:")
    for path in sealed[: len(inputs) * 2]:
        print(f"  {path.name} <- {path.parent.name}")
    print("sealed-summary additions, first artifact-reference order:")
    for path in sealed[len(inputs) * 2 :]:
        print(f"  {path.name}")
    print(f"count: sealed={len(sealed)}")


def _reducer_report(inputs: tuple[EvaluationInput, ...]) -> None:
    sealed = reduce_evaluations(inputs)
    print("REDUCER")
    print(
        "sealed order:",
        sealed.select("evaluation_ordinal", "evaluation_id").rows(),
    )
    print(
        "checkpoint-derived columns:",
        "smooth_l1_loss, natural_log_mae, natural_log_mse",
    )


def _malformed_report(root: Path, inputs: tuple[EvaluationInput, ...]) -> None:
    print("MALFORMED INPUTS")
    scenarios = (
        ("extra JSON field", _add_extra_field),
        ("wrong Parquet dtype", _change_dtype),
        ("unordered origins", _reverse_origins),
        ("missing required checkpoint", _remove_checkpoint_path),
    )
    for label, mutate in scenarios:
        scenario_root = root / "malformed" / label.replace(" ", "_")
        shutil.copytree(root / "evaluations", scenario_root / "evaluations")
        shutil.copytree(root / "artifacts", scenario_root / "artifacts")
        scenario_inputs = tuple(
            EvaluationInput(
                scenario_root / "evaluations" / source.evaluation_dir.name,
                scenario_root / "artifacts" / source.checkpoint_path.name
                if source.checkpoint_path is not None
                else None,
            )
            for source in inputs
        )
        scenario_inputs = mutate(scenario_inputs)
        try:
            reduce_evaluations(scenario_inputs)
        except AuthorityError as exc:
            print(f"  PASS {label}: {str(exc).splitlines()[0]}")
        else:
            raise AssertionError(f"malformed scenario unexpectedly passed: {label}")


def _add_extra_field(inputs: tuple[EvaluationInput, ...]) -> tuple[EvaluationInput, ...]:
    path = inputs[0].evaluation_dir / "evaluation.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["summary"] = {"forbidden": True}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return inputs


def _change_dtype(inputs: tuple[EvaluationInput, ...]) -> tuple[EvaluationInput, ...]:
    path = inputs[0].evaluation_dir / "observations.parquet"
    frame = pl.read_parquet(path).with_columns(pl.col("origin_block").cast(pl.Int32))
    frame.write_parquet(path)
    return inputs


def _reverse_origins(inputs: tuple[EvaluationInput, ...]) -> tuple[EvaluationInput, ...]:
    path = inputs[0].evaluation_dir / "observations.parquet"
    pl.read_parquet(path).reverse().write_parquet(path)
    return inputs


def _remove_checkpoint_path(
    inputs: tuple[EvaluationInput, ...],
) -> tuple[EvaluationInput, ...]:
    return (EvaluationInput(inputs[0].evaluation_dir), *inputs[1:])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--section",
        choices=("all", "collection", "reducer", "malformed"),
        default="all",
    )
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="spice-issue-35-") as temporary:
        root = Path(temporary)
        inputs = _make_fixture(root)
        if args.section in {"all", "collection"}:
            _collection_report(inputs)
        if args.section in {"all", "reducer"}:
            _reducer_report(inputs)
        if args.section in {"all", "malformed"}:
            _malformed_report(root, inputs)


if __name__ == "__main__":
    main()

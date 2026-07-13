"""Read-only accounting probe over two frozen historical block windows.

These windows were selected after inspecting archived outcomes because they make
the denominator difference visible. They are diagnostics, not proposed protocol
windows and not evidence for the issue-46 clean contract.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

FROZEN_DB_SHA256 = "ba70a8f65e9210edc2cfee63243d69e46f55235f5b78f39d7dd5cdd83bf724b0"
LEGACY_EVENT_SAVINGS_METRIC_ID = "profit_over_baseline"
RUN_IDS = (
    "polygon_lstm_36s_block300_quartile_eval."
    "evaluations-polygon_block300_fee_level_q4_005_82363890.evaluate_baseline",
    "polygon_lstm_36s_block_count_quartile_eval."
    "evaluations-polygon_block1200_fee_level_q1_002_80322090.evaluate_baseline",
)


@dataclass(frozen=True, slots=True)
class FrozenWindow:
    run_id: str
    evaluator_id: str
    sample_count: int
    total_events: int
    archived_mean_event_savings: float
    baseline_fee_per_gas_sum: float
    selected_fee_per_gas_sum: float
    hindsight_fee_per_gas_sum: float

    @property
    def fee_sum_savings_ratio(self) -> float:
        return (
            self.baseline_fee_per_gas_sum - self.selected_fee_per_gas_sum
        ) / self.baseline_fee_per_gas_sum

    @property
    def fee_sum_hindsight_regret_ratio(self) -> float:
        return (
            self.selected_fee_per_gas_sum - self.hindsight_fee_per_gas_sum
        ) / self.baseline_fee_per_gas_sum

    @property
    def fee_sum_hindsight_opportunity_ratio(self) -> float:
        return (
            self.baseline_fee_per_gas_sum - self.hindsight_fee_per_gas_sum
        ) / self.baseline_fee_per_gas_sum


def load(db_path: Path) -> tuple[FrozenWindow, ...]:
    digest = hashlib.sha256(db_path.read_bytes()).hexdigest()
    if digest != FROZEN_DB_SHA256:
        raise RuntimeError(
            "frozen result index identity changed; refusing to reinterpret another database"
        )

    connection = sqlite3.connect(
        f"{db_path.resolve().as_uri()}?mode=ro&immutable=1",
        uri=True,
    )
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise RuntimeError(f"frozen result index integrity failed: {integrity}")
        rows = connection.execute(
            """
            SELECT
                o.run_id,
                o.evaluator_id,
                o.sample_count,
                o.total_events,
                MAX(CASE WHEN m.metric_id = ? THEN m.value END),
                MAX(CASE WHEN m.metric_id = 'baseline_fee_sum' THEN m.value END),
                MAX(CASE WHEN m.metric_id = 'realized_fee_sum' THEN m.value END),
                MAX(CASE WHEN m.metric_id = 'optimum_fee_sum' THEN m.value END)
            FROM result_observations AS o
            JOIN metric_values AS m USING (observation_id)
            WHERE m.source = 'evaluation'
              AND o.run_id IN (?, ?)
            GROUP BY o.observation_id
            ORDER BY o.sample_count
            """,
            (LEGACY_EVENT_SAVINGS_METRIC_ID, *RUN_IDS),
        ).fetchall()
    finally:
        connection.close()

    if len(rows) != len(RUN_IDS):
        raise RuntimeError(f"expected {len(RUN_IDS)} frozen rows, found {len(rows)}")
    return tuple(FrozenWindow(*row) for row in rows)


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    db_path = root / "benchmarks" / "results.sqlite"
    windows = load(db_path)

    print("FROZEN HISTORICAL WINDOW ACCOUNTING")
    print(f"database: {db_path}")
    print(f"sha256: {FROZEN_DB_SHA256}")
    print(
        "status: outcome-selected accounting diagnostics under old current-row/Poisson "
        "semantics; not clean-contract results"
    )
    for window in windows:
        assert (
            abs(
                window.fee_sum_savings_ratio
                + window.fee_sum_hindsight_regret_ratio
                - window.fee_sum_hindsight_opportunity_ratio
            )
            < 1e-12
        )
        assert window.archived_mean_event_savings < 0 < window.fee_sum_savings_ratio
        print()
        print(f"window: {window.run_id}")
        print(
            f"  samples={window.sample_count}; sampled events={window.total_events}; "
            f"evaluator={window.evaluator_id}"
        )
        print(
            "  archived mean per-event base-fee savings ratio: "
            f"{window.archived_mean_event_savings:.8%}"
        )
        print(
            "  reconstructed unweighted fee-per-gas ratio of sums: "
            f"{window.fee_sum_savings_ratio:.8%}"
        )
        print(
            "  reconstructed hindsight opportunity / regret: "
            f"{window.fee_sum_hindsight_opportunity_ratio:.8%} / "
            f"{window.fee_sum_hindsight_regret_ratio:.8%}"
        )

    print()
    print(
        "Finding: both frozen rows change sign when the reducer changes. The index has "
        "no transaction-gas vector, eligible-origin rows, raw tie sets, or clean-contract "
        "predictions, so it cannot compute or validate the proposed primary metrics."
    )


if __name__ == "__main__":
    main()

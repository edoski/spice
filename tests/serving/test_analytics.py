from __future__ import annotations

from spice.serving.analytics import ServingAnalyticsStore
from spice.serving.schemas import ObserveTransactionResponse, PredictionResponse


def _prediction() -> PredictionResponse:
    return PredictionResponse(
        request_id="req_1",
        chain_name="sepolia",
        chain_id=11155111,
        artifact_id="art_1",
        observed_block=100,
        observed_timestamp=1_700_000_000,
        baseline_block=101,
        broadcast_after_block=102,
        target_block=103,
        target_timestamp_estimate=1_700_000_036,
        selected_offset=2,
        recommended_wait_seconds=24,
        expires_at_unix=1_700_000_600,
        support_start_block=80,
        support_end_block=101,
    )


def test_analytics_records_prediction_and_observation(tmp_path) -> None:
    store = ServingAnalyticsStore(tmp_path / "serving.sqlite")
    store.record_prediction(_prediction())

    assert store.get_prediction("req_1").baseline_block == 101

    store.record_observation(
        ObserveTransactionResponse(
            request_id="req_1",
            tx_hash="0xabc",
            included_block=103,
            gas_used="21000",
            baseline_block=101,
            baseline_fee_wei="210000",
            model_fee_wei="105000",
            savings_wei="105000",
            savings_percent=50.0,
        )
    )

    analytics = store.analytics()

    assert analytics.totals.run_count == 1
    assert analytics.totals.savings_total_wei == "105000"
    assert analytics.totals.win_count == 1
    assert analytics.rows[0].tx_hash == "0xabc"

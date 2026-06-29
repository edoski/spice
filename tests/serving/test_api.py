from __future__ import annotations

from spice.serving.api import create_app
from spice.serving.schemas import (
    AnalyticsResponse,
    AnalyticsTotals,
    ModelInfoResponse,
    ObserveTransactionResponse,
    PredictionResponse,
)


class FakeService:
    def model_info(self) -> ModelInfoResponse:
        return ModelInfoResponse(
            chain_name="sepolia",
            chain_id=11155111,
            artifact_id="art_1",
            model_family="lstm",
            max_delay_seconds=36,
            slot_spacing_seconds=12.0,
            demo_contract_address="0x0000000000000000000000000000000000000001",
        )

    async def predict(self, _payload) -> PredictionResponse:
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

    async def observe_transaction(self, request_id, _payload) -> ObserveTransactionResponse:
        return ObserveTransactionResponse(
            request_id=request_id,
            tx_hash="0xabc",
            included_block=103,
            gas_used="21000",
            baseline_block=101,
            baseline_fee_wei="210000",
            model_fee_wei="105000",
            savings_wei="105000",
            savings_percent=50.0,
        )

    def analytics(self) -> AnalyticsResponse:
        return AnalyticsResponse(
            totals=AnalyticsTotals(
                run_count=0,
                baseline_fee_total_wei="0",
                model_fee_total_wei="0",
                savings_total_wei="0",
                savings_percent=0.0,
                win_count=0,
            ),
            rows=[],
        )


def test_fastapi_app_registers_mvp_routes() -> None:
    app = create_app(FakeService())

    paths = {route.path for route in app.routes}

    assert "/health" in paths
    assert "/v1/model" in paths
    assert "/v1/predictions" in paths
    assert "/v1/transactions/{request_id}/observe" in paths
    assert "/v1/analytics" in paths

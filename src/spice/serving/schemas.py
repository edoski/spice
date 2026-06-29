"""Serving API DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ServingModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ServingModel):
    status: str


class ModelInfoResponse(ServingModel):
    chain_name: str
    chain_id: int
    artifact_id: str
    model_family: str
    max_delay_seconds: int
    slot_spacing_seconds: float
    demo_contract_address: str


class PredictionRequest(ServingModel):
    max_wait_seconds: int = Field(ge=0)


class PredictionResponse(ServingModel):
    request_id: str
    chain_name: str
    chain_id: int
    artifact_id: str
    observed_block: int
    observed_timestamp: int
    baseline_block: int
    broadcast_after_block: int
    target_block: int
    target_timestamp_estimate: int
    selected_offset: int
    recommended_wait_seconds: int
    expires_at_unix: int
    support_start_block: int
    support_end_block: int


class ObserveTransactionRequest(ServingModel):
    tx_hash: str


class ObserveTransactionResponse(ServingModel):
    request_id: str
    tx_hash: str
    included_block: int
    gas_used: str
    baseline_block: int
    baseline_fee_wei: str
    model_fee_wei: str
    savings_wei: str
    savings_percent: float


class AnalyticsTotals(ServingModel):
    run_count: int
    baseline_fee_total_wei: str
    model_fee_total_wei: str
    savings_total_wei: str
    savings_percent: float
    win_count: int


class AnalyticsRow(ServingModel):
    request_id: str
    created_at: str
    tx_hash: str | None
    wait_seconds: int
    baseline_block: int
    included_block: int | None
    baseline_fee_wei: str | None
    model_fee_wei: str | None
    savings_wei: str | None
    savings_percent: float | None


class AnalyticsResponse(ServingModel):
    totals: AnalyticsTotals
    rows: list[AnalyticsRow]

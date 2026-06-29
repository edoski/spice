"""FastAPI adapter for Sepolia serving."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from .analytics import ServingAnalyticsStore
from .config import ServingConfig, load_serving_config
from .inference import OnlinePredictionService
from .live_blocks import build_live_sepolia_client
from .runtime import load_serving_runtime
from .schemas import (
    AnalyticsResponse,
    HealthResponse,
    ModelInfoResponse,
    ObserveTransactionRequest,
    ObserveTransactionResponse,
    PredictionRequest,
    PredictionResponse,
)


def create_app(service: OnlinePredictionService | None = None) -> FastAPI:
    app = FastAPI(title="SPICE Sepolia Serving API")
    if service is not None:
        app.state.service = service

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/v1/model", response_model=ModelInfoResponse)
    async def model_info(request: Request) -> ModelInfoResponse:
        return _service(request).model_info()

    @app.post("/v1/predictions", response_model=PredictionResponse)
    async def predict(
        request: Request,
        payload: PredictionRequest,
    ) -> PredictionResponse:
        try:
            return await _service(request).predict(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/v1/transactions/{request_id}/observe",
        response_model=ObserveTransactionResponse,
    )
    async def observe_transaction(
        request_id: str,
        request: Request,
        payload: ObserveTransactionRequest,
    ) -> ObserveTransactionResponse:
        try:
            return await _service(request).observe_transaction(request_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/analytics", response_model=AnalyticsResponse)
    async def analytics(request: Request) -> AnalyticsResponse:
        return _service(request).analytics()

    return app


def build_service(config: ServingConfig | None = None) -> OnlinePredictionService:
    resolved_config = load_serving_config() if config is None else config
    runtime = load_serving_runtime(resolved_config)
    return OnlinePredictionService(
        runtime=runtime,
        live_blocks=build_live_sepolia_client(resolved_config, runtime.source_requirements),
        analytics=ServingAnalyticsStore(resolved_config.analytics_db_path),
    )


def _service(request: Request) -> OnlinePredictionService:
    service = getattr(request.app.state, "service", None)
    if service is None:
        service = build_service()
        request.app.state.service = service
    return service


app = create_app()

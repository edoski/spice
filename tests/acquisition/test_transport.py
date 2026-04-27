from __future__ import annotations

import asyncio

import aiohttp
from web3.providers.rpc.utils import ExceptionRetryConfiguration

from spice.acquisition.rpc.transport import RPC_USER_AGENT, ManagedAsyncHTTPProvider


def test_managed_async_http_provider_retries_batch_transport_errors(monkeypatch) -> None:
    provider = ManagedAsyncHTTPProvider(
        "http://localhost:8545",
        exception_retry_configuration=ExceptionRetryConfiguration(
            errors=[aiohttp.ClientError],
            retries=2,
            backoff_factor=0.0,
        ),
    )
    attempts = 0

    async def _fake_post_request(endpoint_uri: str, data: bytes, **kwargs: object) -> bytes:
        del endpoint_uri, data, kwargs
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise aiohttp.ClientPayloadError("short response")
        return b'[{"jsonrpc":"2.0","id":1,"result":"ok"}]'

    monkeypatch.setattr(
        provider._request_session_manager,
        "async_make_post_request",
        _fake_post_request,
    )
    monkeypatch.setattr(provider, "encode_batch_rpc_request", lambda requests: b"[]")

    response = asyncio.run(provider.make_batch_request([("eth_test", [])]))

    assert attempts == 2
    assert response == [{"jsonrpc": "2.0", "id": 1, "result": "ok"}]


def test_managed_async_http_provider_sets_user_agent_header() -> None:
    provider = ManagedAsyncHTTPProvider("http://localhost:8545")

    assert provider._request_kwargs_mapping()["headers"]["User-Agent"] == RPC_USER_AGENT


def test_managed_async_http_provider_preserves_existing_headers() -> None:
    provider = ManagedAsyncHTTPProvider(
        "http://localhost:8545",
        request_kwargs={"headers": {"X-Test": "1"}},
    )

    headers = provider._request_kwargs_mapping()["headers"]
    assert headers["User-Agent"] == RPC_USER_AGENT
    assert headers["X-Test"] == "1"

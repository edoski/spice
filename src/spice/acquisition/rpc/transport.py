"""HTTP JSON-RPC transport helpers for acquisition."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from web3 import AsyncWeb3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import AsyncHTTPProvider
from web3.providers.rpc.utils import ExceptionRetryConfiguration
from web3.types import RPCEndpoint, RPCResponse

from ...config.models import ChainSpec, ResolvedRpcEndpointConfig

RPC_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) "
    "Gecko/20100101 Firefox/125.0"
)


def _retry_configuration(rpc_endpoint: ResolvedRpcEndpointConfig) -> ExceptionRetryConfiguration:
    return ExceptionRetryConfiguration(
        errors=[aiohttp.ClientError, OSError, TimeoutError],
        retries=rpc_endpoint.retry_count,
        backoff_factor=rpc_endpoint.backoff_factor,
    )


class RetryingBatchAsyncHTTPProvider(AsyncHTTPProvider):
    async def make_batch_request(
        self,
        batch_requests: list[tuple[RPCEndpoint, Any]],
    ) -> list[RPCResponse] | RPCResponse:
        if self.exception_retry_configuration is None:
            return await super().make_batch_request(batch_requests)
        for attempt in range(self.exception_retry_configuration.retries):
            try:
                return await super().make_batch_request(batch_requests)
            except tuple(self.exception_retry_configuration.errors):
                if attempt < self.exception_retry_configuration.retries - 1:
                    await asyncio.sleep(
                        self.exception_retry_configuration.backoff_factor * 2**attempt
                    )
                    continue
                raise
        return await super().make_batch_request(batch_requests)


def build_async_web3(rpc_endpoint: ResolvedRpcEndpointConfig, chain: ChainSpec) -> AsyncWeb3:
    headers = {"Content-Type": "application/json", "User-Agent": RPC_USER_AGENT}
    web3 = AsyncWeb3(
        RetryingBatchAsyncHTTPProvider(
            rpc_endpoint.url,
            request_kwargs={
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=rpc_endpoint.timeout_seconds),
            },
            exception_retry_configuration=_retry_configuration(rpc_endpoint),
        )
    )
    if chain.runtime.uses_poa_extra_data:
        web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return web3

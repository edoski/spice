"""Thin provider helpers built on top of runtime configuration."""

from __future__ import annotations

import requests
from web3 import Web3
from web3.providers.rpc.rpc import ExceptionRetryConfiguration

from ..core.config import ChainName, ProviderConfig


def build_web3(provider: ProviderConfig, chain_name: ChainName) -> Web3:
    retry_configuration = ExceptionRetryConfiguration(
        errors=[requests.RequestException, OSError, TimeoutError],
        retries=provider.retry_count,
        backoff_factor=provider.backoff_factor,
    )
    http_provider = Web3.HTTPProvider(
        provider.endpoint_for(chain_name),
        request_kwargs={"timeout": provider.timeout_seconds},
        exception_retry_configuration=retry_configuration,
    )
    return Web3(http_provider)


def redact_sensitive_text(text: str, provider: ProviderConfig) -> str:
    redacted = text
    for sensitive_value in provider.sensitive_values():
        redacted = redacted.replace(sensitive_value, "***")
    return redacted

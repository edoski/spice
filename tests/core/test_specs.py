from __future__ import annotations

import pytest
from pydantic import BaseModel

from spice.core.config_model import ConfigModel
from spice.core.errors import ConfigResolutionError
from spice.core.specs import owner_payload, validate_owner_config


class _OwnerConfig(ConfigModel):
    id: str


class _OtherModel(BaseModel):
    id: str


def test_owner_payload_rejects_non_mapping_payloads() -> None:
    with pytest.raises(ConfigResolutionError):
        owner_payload([], owner="owner", config_type=_OwnerConfig)


def test_owner_payload_rejects_unowned_base_models() -> None:
    with pytest.raises(ConfigResolutionError):
        owner_payload(_OtherModel(id="x"), owner="owner", config_type=_OwnerConfig)


def test_validate_owner_config_wraps_validation_errors() -> None:
    with pytest.raises(ConfigResolutionError):
        validate_owner_config({}, _OwnerConfig)

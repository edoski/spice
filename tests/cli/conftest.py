from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

_CONF_ROOT = Path(__file__).resolve().parents[2] / "src" / "spice" / "conf"


@pytest.fixture
def write_override(tmp_path: Path):
    def _write(
        payload: dict[str, object],
        *,
        name: str = "override.yaml",
    ) -> Path:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path

    return _write


@pytest.fixture
def isolate_conf_root(tmp_path: Path, monkeypatch):
    def _isolate() -> Path:
        from spice.config import registry

        target = tmp_path / "conf"
        shutil.copytree(_CONF_ROOT, target)
        monkeypatch.setattr(registry, "_CONF_ROOT", target)
        return target

    return _isolate

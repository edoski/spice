from pathlib import Path

from spice_temporal.config import ExperimentConfig


def test_config_loads() -> None:
    config = ExperimentConfig.from_yaml(Path("configs/baseline.yaml"))
    assert config.lookback_seconds == 600
    assert config.window_seconds == [12, 24, 36]
    assert len(config.chains) == 3

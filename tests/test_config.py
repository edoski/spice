import unittest
from pathlib import Path

from spice_temporal.config import ExperimentConfig


class ConfigTestCase(unittest.TestCase):
    def test_config_loads(self) -> None:
        config = ExperimentConfig.from_yaml(Path("configs/baseline.yaml"))
        self.assertEqual(config.lookback_seconds, 600)
        self.assertEqual(config.window_seconds, [12, 24, 36])
        self.assertEqual(len(config.chains), 3)


if __name__ == "__main__":
    unittest.main()

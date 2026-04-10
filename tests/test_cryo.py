import os
import shlex
import unittest
from pathlib import Path
from unittest.mock import patch

from spice_temporal.config import ChainConfig, ChainName, ExperimentConfig, PullConfig
from spice_temporal.cryo import (
    build_cryo_args,
    build_cryo_command,
    build_pull_plan,
    evaluation_range,
)
from spice_temporal.rpc_providers import RpcProviderName, resolve_rpc_provider


class CryoPlanTestCase(unittest.TestCase):
    def test_pull_plan_includes_rate_controls(self) -> None:
        config = ExperimentConfig.from_yaml(Path("configs/pilots/ethereum-36s.yaml"))
        with patch.dict(os.environ, {"ETHEREUM_RPC_URL": "https://rpc.example.test"}, clear=False):
            plans = build_pull_plan(
                config,
                provider=resolve_rpc_provider(
                    RpcProviderName.DIRECT,
                    chains=(ChainName.ETHEREUM,),
                ),
            )
        self.assertEqual(len(plans), 1)
        command = plans[0].command
        self.assertIn("--requests-per-second 10", command)
        self.assertIn("--max-concurrent-requests 2", command)
        self.assertIn("--max-concurrent-chunks 1", command)

    def test_command_string_and_args_share_one_command_spec(self) -> None:
        chain = ChainConfig(
            name="ethereum",
            chain_id=1,
            block_time_seconds=12.0,
            history_days=1,
        )
        pull = PullConfig(
            requests_per_second=10,
            max_concurrent_requests=2,
            max_concurrent_chunks=1,
        )
        output_dir = Path("artifacts/raw/ethereum/history")
        with patch.dict(os.environ, {"ETHEREUM_RPC_URL": "https://rpc.example.test"}, clear=False):
            provider = resolve_rpc_provider(
                RpcProviderName.DIRECT,
                chains=(ChainName.ETHEREUM,),
            )
            args = build_cryo_args(
                chain,
                pull,
                output_dir,
                evaluation_range(),
                provider=provider,
                overwrite=True,
            )
            command = build_cryo_command(
                chain,
                pull,
                output_dir,
                evaluation_range(),
                provider=provider,
                overwrite=True,
            )

        self.assertEqual(
            shlex.split(command.replace("$ETHEREUM_RPC_URL", "https://rpc.example.test")),
            args,
        )

    def test_command_uses_selected_publicnode_provider(self) -> None:
        chain = ChainConfig(
            name="ethereum",
            chain_id=1,
            block_time_seconds=12.0,
            history_days=1,
        )
        pull = PullConfig(
            requests_per_second=10,
            max_concurrent_requests=2,
            max_concurrent_chunks=1,
        )
        output_dir = Path("artifacts/raw/ethereum/history")
        provider = resolve_rpc_provider(
            RpcProviderName.PUBLICNODE,
            chains=(ChainName.ETHEREUM,),
        )

        args = build_cryo_args(
            chain,
            pull,
            output_dir,
            evaluation_range(),
            provider=provider,
            overwrite=True,
        )
        command = build_cryo_command(
            chain,
            pull,
            output_dir,
            evaluation_range(),
            provider=provider,
            overwrite=True,
        )

        self.assertEqual(shlex.split(command), args)
        self.assertIn("https://ethereum-rpc.publicnode.com", command)


if __name__ == "__main__":
    unittest.main()

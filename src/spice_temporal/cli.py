"""Command-line interface for the SPICE temporal baseline project."""

from __future__ import annotations

import argparse
from pathlib import Path

from spice_temporal.config import ExperimentConfig

def show_config(config_path: Path) -> None:
    """Print a quick summary of the experiment configuration."""
    config = ExperimentConfig.from_yaml(config_path)
    print(f"Output root: {config.output_root}")
    print(f"Windows: {config.window_seconds}")
    print(f"Lookback: {config.lookback_seconds}s")
    print("Chains:")
    for chain in config.chains:
        print(
            f"  - {chain.name}: chain_id={chain.chain_id}, "
            f"nominal_block_time={chain.nominal_block_time_seconds}s, "
            f"rpc_env_var={chain.rpc_env_var}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spice-temporal")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_config_parser = subparsers.add_parser(
        "show-config",
        help="Print a quick summary of the experiment configuration.",
    )
    show_config_parser.add_argument("config_path", type=Path)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "show-config":
        show_config(args.config_path)


if __name__ == "__main__":
    main()

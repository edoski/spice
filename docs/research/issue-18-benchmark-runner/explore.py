"""Thin terminal shell for the Issue 18 runner-boundary prototype."""

from __future__ import annotations

import argparse
import csv
import sys

from prototype_logic import approved_stages, counts, designs, evidence_rows, minimal_batch

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"


def render(section: str) -> str:
    stages = approved_stages()
    lines = [f"{BOLD}Issue 18 runner prototype — {section}{RESET}", ""]
    if section == "matrices":
        for stage in stages:
            kinds = ", ".join(sorted({item.workflow for item in stage.requests}))
            lines.append(
                f"{stage.name:20} new={len(stage.requests):2} "
                f"reused={stage.reused_artifact_count:2} "
                f"workflow={kinds:8} gate={stage.owner_gate_after or '-'}"
            )
        lines.append("")
        lines.extend(f"{key:28} {value}" for key, value in counts(stages).items())
    elif section == "explicit":
        lines.extend(
            [
                "Named functions construct complete typed requests only after each owner gate.",
                "Each stage passes an ordinary tuple to the Issue-30/execution-owned direct plan.",
                "Testing loads evaluations/<evaluation_id>.json for the 45 exact request IDs.",
                "Accelerator parity contributes only the approved Issue-40 report pointer.",
            ]
        )
    elif section == "batch":
        batches = minimal_batch(stages)
        edge_count = sum(len(entry.after_labels) for _, batch in batches for entry in batch)
        lines.extend(
            [
                f"Batch plans: {len(batches)}",
                f"Batch entries: {sum(len(batch) for _, batch in batches)}",
                f"Useful in-stage dependency edges: {edge_count}",
                "Result: the extra after-label graph has no surviving work.",
            ]
        )
    elif section == "designs":
        lines.append(
            "name                          files  lines  types  interfaces  shapes  scheduling"
        )
        for design in designs():
            lines.append(
                f"{design.name:29} {design.production_files:5} {design.production_lines:6} "
                f"{design.owned_types:6} {design.owned_interfaces:11} "
                f"{design.persistent_shapes:7} {design.scheduling_concepts:11}"
            )
            lines.append(f"  {DIM}{design.note}{RESET}")
    return "\n".join(lines)


def write_tsv() -> None:
    writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    writer.writerow(("label", "artifact_id", "evaluation_id", "record_path"))
    for row in evidence_rows(approved_stages()):
        writer.writerow((row.label, row.artifact_id, row.evaluation_id, row.record_path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="print every comparison")
    parser.add_argument("--tsv", action="store_true", help="print the simple evidence table")
    args = parser.parse_args()
    if args.tsv:
        write_tsv()
        return
    if args.report:
        sections = ("matrices", "explicit", "batch", "designs")
        print("\n\n".join(render(section) for section in sections))
        return
    sections = {"m": "matrices", "e": "explicit", "b": "batch", "d": "designs"}
    selected = "matrices"
    while True:
        print("\x1b[2J\x1b[H" + render(selected))
        menu = (
            f"\n{BOLD}[m]{RESET} matrices  {BOLD}[e]{RESET} explicit  "
            f"{BOLD}[b]{RESET} batch  {BOLD}[d]{RESET} designs  "
            f"{BOLD}[q]{RESET} quit"
        )
        print(menu)
        key = input("> ").strip().lower()
        if key == "q":
            return
        selected = sections.get(key, selected)


if __name__ == "__main__":
    main()

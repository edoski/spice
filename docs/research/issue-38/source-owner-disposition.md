# Source-owner disposition

This file is explicitly nonnormative historical planning evidence for the clean-break repository cut. It records one frozen owner for each tracked legacy path or registered surface present at creation. It is not runtime authority or status, a manifest, an inventory service, a compatibility map, a registry, a scanner, a CI input, or a permanent absence test. It remains byte-unchanged through S24.

Each ledger row has exactly four fields. A bare path atom owns the entire tracked path only when no qualified atom exists for that path. For a mixed file, `path :: unqualified remainder` owns only content not named by a sibling qualified atom, while `path :: exact symbol or registration` owns only the named surface; these atoms do not overlap. An externally visible registered atom uses `surface :: kind :: exact identifier`; it records the registered interface, not external state or a file. The disposition is exactly `replace`, `delete`, or `preserve solely as non-runtime historical evidence`. A replacement is named only where applicable.

The ledger excludes active unchanged `.gitignore`, `apps/mobile/tsconfig.json`, and `docs/agents/domain.md`, `docs/agents/issue-tracker.md`, and `docs/agents/triage-labels.md`; this D4 file itself; untracked or ignored material; external files or state; raw SQLite/catalog bytes; cwd-local `REMOTE.yaml`; and future implementation additions. Only frozen implementation keys may own rows; reviews, readiness, scientific-execution, manual, custody, and export gates own none. Exact path and frozen-title bytes may contain historical issue names or references; there is no issue-number, ticket-number, review, gate, status, or mutable-mapping field.

## Ledger

| Exact tracked legacy path or registered surface | Disposition | Owner key and exact title | Named replacement |
|---|---|---|---|
| AGENTS.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | AGENTS.md :: stable repository-relative tracker locator |
| apps/mobile/app.json | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | apps/mobile/app.json |
| apps/mobile/app/_layout.tsx | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/App.tsx |
| apps/mobile/app/analytics.tsx | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/App.tsx |
| apps/mobile/app/index.tsx | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/App.tsx |
| apps/mobile/app/wallet.tsx | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/App.tsx |
| apps/mobile/package-lock.json | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | apps/mobile/package-lock.json |
| apps/mobile/package.json | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | apps/mobile/package.json |
| apps/mobile/src/api.ts | replace | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/src/inference.ts |
| apps/mobile/src/config.ts | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/src/inference.ts |
| apps/mobile/src/format.ts | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/src/inference.ts |
| apps/mobile/src/scheduler.ts | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/src/inference.ts |
| apps/mobile/src/sepolia.ts | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/src/inference.ts |
| apps/mobile/src/types.ts | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/src/inference.ts |
| apps/mobile/src/wallet.ts | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | apps/mobile/src/inference.ts |
| ARCHITECTURE.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | ARCHITECTURE.md |
| ARCHIVE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/README.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/.keep | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/merge_ethereum_pectra_jun20_corpus.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_delay_degradation_figures.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_edge_case_figures.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_ethereum_pectra_fee_scatter.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_ethereum_pectra_jun20_lstm_edge_figures.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_lstm_block_count_quartile_results.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_lstm_edge_case_class_only_figures.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_lstm_edge_case_cross_chain_figures.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/render_lstm_wall_clock_quartile_results.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/scan_block_count_quartile_windows.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/scan_edge_case_windows.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/scan_ethereum_pectra_edge_case_windows.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/scan_wall_clock_quartile_windows.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/summarize_ethereum_pectra_edge_case_ci.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/summarize_matched_lstm_training_fee_stats.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| benchmarks/scripts/write_evaluation_suite_from_window_csv.py | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| CLEAN_BREAK_TRACKER.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| CONFIGURATION.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| CONTEXT.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | CONTEXT.md |
| contracts/SpiceDemo.sol | delete | S21 — Present S20’s stateless inference boundary through one Expo screen | — |
| docs/adr/0001-root-id-consumer-workflows.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | docs/adr/0001-root-id-consumer-workflows.md |
| docs/adr/0002-config-resolution-hydration-loading.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | docs/adr/0002-config-resolution-hydration-loading.md |
| docs/adr/0003-representation-seam-retained.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | docs/adr/0003-representation-seam-retained.md |
| docs/adr/0004-compiler-materialization-existing-root-vocabulary.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | docs/adr/0004-compiler-materialization-existing-root-vocabulary.md |
| docs/adr/0005-custom-execution-session-retained.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | docs/adr/0005-custom-execution-session-retained.md |
| docs/research/auxiliary-fee-regression-head-conceptual-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/current_block_action_cross_layer_fixture.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/current-block-action-cross-layer-parity-prototype.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/eip1559-equivalent-chain-candidates.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/ethereum-current-row-causality-and-options.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/fixed-block-comparability-and-exhaustive-replay.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue_47_complete_outcome_split_fixture.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/architecture-implementation-docs-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/clean-break-adr-red-team.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/clean-break-config-benchmark-semantics.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/clean-break-crosscut-red-team.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/clean-break-framework-semantics.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/clean-break-persistence-semantics.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/clean-break-verification-semantics.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/clean-break-wayfinder-graph.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-chain-fee-protocol-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-evaluation-statistics-cross-review.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-ml-cross-review.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-ml-lean-alternatives.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-ml-wayfinder-extension-review.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-paper-alignment-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-preprocessing-theory-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-1/temporal-training-evaluation-theory-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-10-configuration-algebra/pydantic-public-seams.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-13-direct-storage/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-15/filesystem-publication-primitives.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-17/prototype_logic.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-17/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-17/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-18-benchmark-runner/audit-and-decision-evidence.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-18-benchmark-runner/explore.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-18-benchmark-runner/native-runner-primitives.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-18-benchmark-runner/prototype_logic.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-18-benchmark-runner/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-19-remote-control-frameworks.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-19/remote-control-contract-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-20/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-21-predictive-diagnostics/auxiliary-regression-theory.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-21-predictive-diagnostics/classification-diagnostics-theory.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-21-predictive-diagnostics/current-code-reducer-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-21-predictive-diagnostics/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-21-predictive-diagnostics/red-team.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-21-predictive-diagnostics/torchmetrics-implementation-comparison.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-22/owner-decisions.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-23/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-23/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-23/paper-model-family-alignment.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-23/prototype_task.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-23/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-23/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-24/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-24/framework-native-common-path.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/direct_candidate.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/lightning_candidate.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/lightning-native-checkpoint-artifact-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/single_artifact_prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-26/task_fixture.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-27/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-27/implementation-map.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-27/prototype_logic.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-27/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-27/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-28/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-28/historical_dataset.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-28/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-28/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-29-bounded-hpo/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-29-bounded-hpo/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-29-bounded-hpo/prototype_logic.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-29-bounded-hpo/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-29-bounded-hpo/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-30/slurm-ambiguous-submission.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-31/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-31/preparation.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-31/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-31/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-32/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-32/uvicorn-role.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-33/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-34/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-35/current-code-and-authority-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-35/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-35/prototype_logic.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-35/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-35/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-39/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-41/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-43/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-43/dependent-completeness-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-43/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-43/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-43/seam.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-45/avalanche-modern-forming-block-fee.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-45/polygon-modern-forming-block-fee.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-causal-preprocessing-split-theory.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-chain-schema-feature-availability.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-current-pipeline-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-ethereum-regime-anchor-redteam.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-owner-decisions.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-polygon-regime-anchor-redteam.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-red-team-review.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-regime-anchor-redteam-synthesis.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-regime-suffix-routing-redteam.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-47/issue-47-three-role-split-theory.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/census_descriptor_logic.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/census-descriptor-prototype.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/census-stratification-methodology.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/current-code-and-frozen-evidence-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/explore_census_descriptors.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/explore_fixture.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/fixture_semantics.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/full-census-condition-view-methodology.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/full-range-regime-conditioning-code-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/k-grid-red-team.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/legacy-window-selector-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/methodological-estimands.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/obsidian-window-method-reconstruction.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/representative_frozen_window.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-48-temporal-evaluation/thesis-alignment-red-team.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-49-temporal-baseline/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-51/file-disposition-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-51/prototype.html | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-53/chain-regime-results-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-55/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-56/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-56/placement_logic.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-56/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-56/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-58-target-coordinate/current-code.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-58-target-coordinate/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-58-target-coordinate/paper-redteam.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-59/decision-contract.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-59/name-red-team.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-59/paper-and-reference-system-attribution.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-59/technical-rename-boundary.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-60-priority-fee-extension/decision.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-61-hpo-framework-comparison/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-62-training-runtime-numerics/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-63/current-inventory.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-63/prototype.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-63/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-63/surface.py | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-64/README.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-78/defensive-integrity-machinery-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-8/evaluation-suite-data-findings.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-8/inventory-redteam-findings.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/issue-8/ticket-8-research-script-inventory.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/modern-regime-coverage-and-evidence-periods.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/remote-execution-supported-interfaces-audit.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/research-evaluation-publication-assets-inventory.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/rpc-retry-finality-alternatives.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/spice-pre-break-evidence-baseline.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/spice-pre-break-evidence-manifest.tsv | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/target-filesystem-root-journal-constraints.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| docs/research/total-loss-economic-objective-ab-evidence.md | preserve solely as non-runtime historical evidence | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| PROGRESS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| pyproject.toml | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | pyproject.toml |
| pyrightconfig.json | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | pyrightconfig.json |
| README.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | README.md |
| src/spice/__init__.py | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | src/fable/__init__.py |
| src/spice/acquisition/__init__.py | replace | S03 — Acquire, finalize, and publish one native Corpus | src/spice/acquisition :: acquire_corpus |
| src/spice/acquisition/ARCHITECTURE.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | src/fable/acquisition/ARCHITECTURE.md |
| src/spice/acquisition/errors.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py :: native Web3 |
| src/spice/acquisition/pull.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/acquisition/rpc/__init__.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py :: native Web3 |
| src/spice/acquisition/rpc/ARCHITECTURE.md | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| src/spice/acquisition/rpc/client.py :: find_first_block_at_or_after, resolve_block_range, plan_window, estimate_recent_block_interval | delete | S04 — Cut over native Corpus acquisition execution and CLI | acquire_corpus fixed request-bound batches |
| src/spice/acquisition/rpc/client.py :: unqualified remainder | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py :: native Web3 |
| src/spice/acquisition/rpc/IMPLEMENTATIONS.md | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| src/spice/acquisition/rpc/transport.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py :: native Web3 |
| src/spice/acquisition/types.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/benchmarks/__init__.py :: active public benchmark exports | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py |
| src/spice/benchmarks/__init__.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/benchmarks/_result_schema.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/_run_state_codec.py :: serializers and JSON/JSONL writers | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| src/spice/benchmarks/_run_state_codec.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/benchmarks/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/benchmarks/collection_resolver.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/collection.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/benchmarks/plan_materialization/__init__.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/benchmarks/plan_materialization/_dependencies.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/plan_materialization/_expansion.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/plan_materialization/_models.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/benchmarks/plan_materialization/_planner.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/plan_materialization/_problem_grid.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/plan_materialization/_roots.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/plan_materialization/_selection.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/result_index.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/result_records.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/benchmarks/runs.py :: create, scan, and write behavior | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| src/spice/benchmarks/runs.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/benchmarks/schema.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/benchmarks/submission.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py :: twelve constructors and four selectors |
| src/spice/cli/app.py :: acquire_command import, registration, help, examples | replace | S04 — Cut over native Corpus acquisition execution and CLI | spice corpus acquire REQUEST.json --rpc-url URL |
| src/spice/cli/app.py :: benchmark, config, show, delete, transfer, refresh, train, tune, evaluate registrations | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | final six-leaf CLI |
| src/spice/cli/app.py :: unqualified remainder | replace | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final plain Typer root |
| src/spice/cli/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/cli/commands/__init__.py | replace | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final plain Typer root |
| src/spice/cli/commands/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/cli/commands/benchmark.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/cli/commands/config.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/cli/commands/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/cli/commands/storage.py :: DatasetDetailOption runs branch | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/cli/commands/storage.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/cli/commands/transfer.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/cli/commands/workflows.py :: acquire_command and Acquire-only imports | replace | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/cli/app.py :: corpus acquire |
| src/spice/cli/commands/workflows.py :: train_command, tune_command, evaluate_command, legacy submission helpers | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | submit plus Study and hidden remote leaves |
| src/spice/cli/commands/workflows.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/cli/errors.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/cli/options.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/cli/options.py :: WorkflowCorpusOption, WorkflowProviderOption, WorkflowStorageRootWriteOption, WorkflowDryRunOption | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/cli/output.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/cli/app.py :: final six-leaf CLI |
| src/spice/conf/__init__.py | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/conf/benchmark/delay_degradation_eth_lstm_beyond_600.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/delay_degradation_eth_polygon_lstm_330_900.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/delay_degradation_extension.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/delay_degradation_lstm_long_extension.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/delay_degradation_short_window_fillin.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/delay_degradation_sweep.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/edge_case_baseline_36s.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/elapsed_position_ablation.yaml | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| src/spice/conf/benchmark/ethereum_pectra_jun20_edge_case_lstm_36s.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/large_capacity_hpo.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/lookback_window_sweep.yaml | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| src/spice/conf/benchmark/lstm_36s_block_count_quartile_eval.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/lstm_36s_block300_quartile_eval.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/lstm_36s_large_polygon_avalanche_edge_eval.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/lstm_36s_matched_training_budget_polygon_avalanche.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/lstm_36s_wall_clock_quartile_eval.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/nov9_cutoff_36s_day_eval.yaml | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| src/spice/conf/benchmark/nov9_cutoff_36s_sweep.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/nov9_cutoff_36s_warm_hpo.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/old_window_comparison_36s.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/priority_fee_ablation.yaml | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| src/spice/conf/benchmark/safe_baseline_grid.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/benchmark/slot_spacing_sweep.yaml | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| src/spice/conf/chain/avalanche.yaml | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| src/spice/conf/chain/ethereum.yaml | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| src/spice/conf/chain/polygon.yaml | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| src/spice/conf/chain/sepolia.yaml | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| src/spice/conf/corpus/avalanche_octane_to_2026_05_17.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/corpus/ethereum_pectra_suffix_2026_05_15_to_2026_06_20.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/corpus/ethereum_pectra_to_2026_05_15.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/corpus/ethereum_pectra_to_2026_06_20.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/corpus/icdcs_2026.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/corpus/polygon_bhilai_to_2026_05_17.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/evaluations/avalanche_octane_1p53m_edge_case_recommended.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/avalanche_octane_1p53m_train_cutoff.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/avalanche_octane_edge_cases.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/avalanche_octane_large_lstm_block_count_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/avalanche_octane_large_lstm_block300_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/avalanche_octane_large_lstm_edge_case_recommended.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/avalanche_octane_large_lstm_wall_clock_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/ethereum_pectra_edge_cases.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/ethereum_pectra_jun20_block_count_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/ethereum_pectra_jun20_block300_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/ethereum_pectra_jun20_edge_case_recommended.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/ethereum_pectra_jun20_wall_clock_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/ethereum_pectra_smoke.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/nov9_2025_2h.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/nov9_2025_day.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/polygon_bhilai_1p53m_edge_case_recommended.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/polygon_bhilai_1p53m_train_cutoff.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/polygon_bhilai_edge_cases.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/polygon_bhilai_large_lstm_block_count_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/polygon_bhilai_large_lstm_block300_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/polygon_bhilai_large_lstm_edge_case_recommended.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluations/polygon_bhilai_large_lstm_wall_clock_quartile.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluator/block_poisson_replay_300.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluator/block_poisson_replay.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/evaluator/poisson_replay.yaml | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| src/spice/conf/execution/disi_l40.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/execution/disi_rtx2080.yaml | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/features/core_fee_dynamics_elapsed_position.yaml | delete | S05 — Construct and scale exact causal feature rows | — |
| src/spice/conf/features/core_fee_dynamics_with_priority_fee.yaml | delete | S05 — Construct and scale exact causal feature rows | — |
| src/spice/conf/features/core_fee_dynamics.yaml | delete | S05 — Construct and scale exact causal feature rows | — |
| src/spice/conf/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/conf/model/lstm.yaml | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| src/spice/conf/model/transformer_lstm.yaml | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| src/spice/conf/model/transformer.yaml | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| src/spice/conf/prediction/icdcs_2026.yaml | delete | S06 — Implement the architecture-neutral Min-Block-Fee task | — |
| src/spice/conf/problem/current_row_nominal.yaml | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| src/spice/conf/problem/current_row_recent_median.yaml | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| src/spice/conf/provider/publicnode.yaml | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/conf/provider/tenderly.yaml | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/conf/split/default.yaml | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| src/spice/conf/surface/current_row_fee_dynamics.yaml :: acquisition section | delete | S04 — Cut over native Corpus acquisition execution and CLI | CorpusRequest plus --rpc-url |
| src/spice/conf/surface/current_row_fee_dynamics.yaml :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| src/spice/conf/training/default.yaml | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| src/spice/conf/tuning_space/lstm_default.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning_space/lstm_fixed_context.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning_space/lstm_large_capacity.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning_space/lstm_warm_large_capacity.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning_space/transformer_large_capacity.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning_space/transformer_lstm_large_capacity.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning_space/transformer_lstm_warm_large_capacity.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning_space/transformer_warm_large_capacity.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning/default.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/conf/tuning/extensive.yaml | delete | S09 — Publish immutable Studies and materialize selected training | — |
| src/spice/config/__init__.py | replace | S01 — Establish strict request/definition values and canonical direct addresses | src/spice/config :: strict request/definition value exports |
| src/spice/config/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/config/group_catalog.py :: ConfigGroup.BENCHMARK and Benchmark GroupSpec | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py |
| src/spice/config/group_catalog.py :: ConfigGroup.CHAIN and Chain GroupSpec | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | three direct Web3 clients |
| src/spice/config/group_catalog.py :: ConfigGroup.CORPUS and Corpus GroupSpec | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | CorpusRequest JSON |
| src/spice/config/group_catalog.py :: ConfigGroup.EVALUATOR, ConfigGroup.EVALUATIONS, and their GroupSpec rows | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | EvaluationRequest |
| src/spice/config/group_catalog.py :: ConfigGroup.EXECUTION and Execution GroupSpec | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | cwd-local REMOTE.yaml |
| src/spice/config/group_catalog.py :: ConfigGroup.FEATURES and Features GroupSpec | delete | S05 — Construct and scale exact causal feature rows | ExperimentSemantics ordered feature tuples |
| src/spice/config/group_catalog.py :: ConfigGroup.MODEL, ConfigGroup.TRAINING, and their GroupSpec rows | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | Definition, Method, and TrainingDefinition |
| src/spice/config/group_catalog.py :: ConfigGroup.PREDICTION and Prediction GroupSpec | delete | S06 — Implement the architecture-neutral Min-Block-Fee task | ExperimentSemantics |
| src/spice/config/group_catalog.py :: ConfigGroup.PROBLEM, ConfigGroup.SPLIT, and their GroupSpec rows | delete | S08 — Prepare exact historical windows as lazy CPU datasets | strict ExperimentSemantics and TrainRequest |
| src/spice/config/group_catalog.py :: ConfigGroup.PROVIDER and Provider GroupSpec | delete | S04 — Cut over native Corpus acquisition execution and CLI | --rpc-url |
| src/spice/config/group_catalog.py :: ConfigGroup.SURFACE and Surface GroupSpec | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON |
| src/spice/config/group_catalog.py :: ConfigGroup.TUNING, ConfigGroup.TUNING_SPACE, and their GroupSpec rows | delete | S09 — Publish immutable Studies and materialize selected training | TuneRequest and MethodSpace |
| src/spice/config/group_catalog.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON and REMOTE.yaml |
| src/spice/config/groups.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON and REMOTE.yaml |
| src/spice/config/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/config/models.py :: active ProblemSpec, SplitConfig, SequenceConfig selection/resolution surfaces | replace | S08 — Prepare exact historical windows as lazy CPU datasets | ExperimentSemantics and fixed role geometry |
| src/spice/config/models.py :: ChainRuntimeSpec and remaining legacy manifest/config decode DTOs/coercers | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/config/models.py :: ChainSpec, ResolvedRpcEndpointConfig, validators | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | lifespan STORAGE_ROOT and three RPC URL strings |
| src/spice/config/models.py :: unqualified remainder | replace | S01 — Establish strict request/definition values and canonical direct addresses | src/spice/config :: strict request/definition value exports |
| src/spice/config/models.py :: WorkflowTask, ArtifactVariant, TimestampWindowSpec, BlockWindowSpec, EvaluationWindowSpecBase, TimestampEvaluationWindowSpec, BlockEvaluationWindowSpec, CorpusSpec, ProblemSpec, SplitConfig, EarlyStoppingConfig, SequenceConfig, TrainingConfig, StudyConfig, ArtifactConfig, ModelWorkflowConfig, TrainConfig, TuneConfig, EvaluateConfig | replace | S01 — Establish strict request/definition values and canonical direct addresses | strict request/definition values and WORKFLOW_REQUEST_ADAPTER |
| src/spice/config/models.py :: WorkflowTask.ACQUIRE, AcquisitionRpcConfig, AcquisitionConfig, ProviderEndpointConfig, ProviderTransportConfig, ProviderSpec, AcquireConfig | delete | S04 — Cut over native Corpus acquisition execution and CLI | CorpusRequest plus rpc_url |
| src/spice/config/resolution.py :: Acquire overload, union member, dispatch branch, imports, _resolve_acquire_config | delete | S04 — Cut over native Corpus acquisition execution and CLI | direct REQUEST.json hydration |
| src/spice/config/resolution.py :: active FEATURES resolution | delete | S05 — Construct and scale exact causal feature rows | strict request hydration |
| src/spice/config/resolution.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON and REMOTE.yaml |
| src/spice/config/resolved_workflows.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON and REMOTE.yaml |
| src/spice/config/selections.py :: AcquireWorkflowSelection and Acquire union/spec members | delete | S04 — Cut over native Corpus acquisition execution and CLI | CorpusRequest |
| src/spice/config/selections.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON and REMOTE.yaml |
| src/spice/config/surfaces.py :: SurfaceAcquisitionFrame and SurfaceFrame.acquisition | delete | S04 — Cut over native Corpus acquisition execution and CLI | CorpusRequest plus --rpc-url |
| src/spice/config/surfaces.py :: SurfaceTrainingFrame, SurfaceTuningFrame, remaining SurfaceFrame fields | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON |
| src/spice/config/surfaces.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON and REMOTE.yaml |
| src/spice/config/typed_groups.py :: CHAIN | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | three direct Web3 clients |
| src/spice/config/typed_groups.py :: CORPUS | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | CorpusRequest JSON |
| src/spice/config/typed_groups.py :: EVALUATOR and EVALUATIONS | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | EvaluationRequest |
| src/spice/config/typed_groups.py :: EXECUTION | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | cwd-local REMOTE.yaml |
| src/spice/config/typed_groups.py :: FEATURES | delete | S05 — Construct and scale exact causal feature rows | ExperimentSemantics ordered feature tuples |
| src/spice/config/typed_groups.py :: MODEL and TRAINING | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | Definition, Method, and TrainingDefinition |
| src/spice/config/typed_groups.py :: PREDICTION | delete | S06 — Implement the architecture-neutral Min-Block-Fee task | ExperimentSemantics |
| src/spice/config/typed_groups.py :: PROBLEM and SPLIT | delete | S08 — Prepare exact historical windows as lazy CPU datasets | strict ExperimentSemantics and TrainRequest |
| src/spice/config/typed_groups.py :: PROVIDER | delete | S04 — Cut over native Corpus acquisition execution and CLI | --rpc-url |
| src/spice/config/typed_groups.py :: SURFACE | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON |
| src/spice/config/typed_groups.py :: TUNING and TUNING_SPACE | delete | S09 — Publish immutable Studies and materialize selected training | TuneRequest and MethodSpace |
| src/spice/config/typed_groups.py :: unqualified remainder | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON and REMOTE.yaml |
| src/spice/config/workflow_snapshots.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/core/__init__.py | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | src/fable/core/__init__.py |
| src/spice/core/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/core/async_runtime.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | asyncio.run(acquire_corpus(...)) |
| src/spice/core/config_model.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/core/constants.py :: MODEL_STATE_FILENAME and TRAINING_CHECKPOINT_FILENAME | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | artifacts/<artifact_id>.ckpt |
| src/spice/core/constants.py :: unqualified remainder | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | src/fable/core/constants.py |
| src/spice/core/errors.py :: legacy reader-only error classes | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/core/errors.py :: unqualified remainder | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | src/fable/core/errors.py |
| src/spice/core/files.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/core/rendering.py | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| src/spice/core/reporting.py | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| src/spice/core/specs.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/core/validation.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/corpus/__init__.py | replace | S02 — Load and validate one canonical Corpus | src/spice/corpus :: Corpus and load_corpus |
| src/spice/corpus/acquisition_stage.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/corpus/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/corpus/assembly.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/corpus/contract.py :: CanonicalBlockFieldSpec, CANONICAL_BLOCK_FIELDS, BLOCK_SCHEMA, BLOCK_COLUMNS, REQUIRED_BLOCK_COLUMNS, _validate_contract, validate_block_frame, _select_canonical_columns | replace | S02 — Load and validate one canonical Corpus | Corpus strict seven-column schema validation |
| src/spice/corpus/contract.py :: RpcBlock, CanonicalBlockRow, _as_int, _optional_int, build_canonical_block_row, canonicalize_block_frame | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py :: private seven-field extraction |
| src/spice/corpus/contract.py :: unqualified remainder | replace | S02 — Load and validate one canonical Corpus | src/spice/corpus :: Corpus, load_corpus, candidate validation |
| src/spice/corpus/coverage.py | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| src/spice/corpus/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/corpus/io.py :: _is_hidden_relative_path, iter_block_files, _scan_block_dataset, _read_block_dataset, load_block_frame | replace | S02 — Load and validate one canonical Corpus | load_corpus over one exact blocks.parquet |
| src/spice/corpus/io.py :: unqualified remainder | replace | S02 — Load and validate one canonical Corpus | src/spice/corpus :: Corpus, load_corpus, candidate validation |
| src/spice/corpus/io.py :: write_block_file | delete | S04 — Cut over native Corpus acquisition execution and CLI | acquire_corpus private chunk/candidate publication |
| src/spice/corpus/metadata.py :: CorpusManifest, ChainMetadata, split/materialization/source DTOs, validators | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/corpus/metadata.py :: ProviderMetadata, AcquisitionConfigSnapshot, AcquireRunFacts, CorpusAcquisitionRuntimeMetadata, AcquireRunRecord, provider_metadata, compact_validation_report, split_manifest, acquisition_settings, acquisition_runtime_metadata, build_dataset_manifest, build_acquire_run_record, CorpusAcquisitionSourceRequirements.fingerprint | delete | S04 — Cut over native Corpus acquisition execution and CLI | Corpus and CorpusRequest |
| src/spice/corpus/metadata.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/corpus/planning.py :: CORE_CORPUS_SOURCE_COLUMNS | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py :: private seven-field extraction |
| src/spice/corpus/planning.py :: unqualified remainder | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/corpus/split_materialization/__init__.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/corpus/split_materialization/_materializer.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/corpus/split_materialization/_models.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/corpus/split_materialization/_parquet_io.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/corpus/validation.py :: active block-frame summary, contiguous/window validation, and report construction | replace | S02 — Load and validate one canonical Corpus | package-private Corpus candidate validator |
| src/spice/corpus/validation.py :: unqualified remainder | replace | S02 — Load and validate one canonical Corpus | src/spice/corpus :: Corpus, load_corpus, candidate validation |
| src/spice/corpus/validation.py :: ValidationStatus reader value | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/evaluation/__init__.py :: active evaluator/compiler/replay exports | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | evaluate |
| src/spice/evaluation/__init__.py :: unqualified remainder | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/evaluation/_temporal_replay_metric_catalog.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/evaluation/ARCHITECTURE.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | src/fable/evaluation/ARCHITECTURE.md |
| src/spice/evaluation/block_poisson_replay.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/evaluation/config.py :: active evaluator and evaluation-suite runtime surfaces | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | EvaluationRequest |
| src/spice/evaluation/config.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/evaluation/contracts.py :: active evaluator contract and EvaluationSummary construction surfaces | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | EvaluationRequest and observations |
| src/spice/evaluation/contracts.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/evaluation/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/evaluation/poisson_replay.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/evaluation/registry.py :: active evaluator registry/compiler | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | evaluate |
| src/spice/evaluation/registry.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/evaluation/temporal_accounting.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/evaluation/temporal_replay_results.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/evaluation/temporal_replay_runner.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/execution/__init__.py | replace | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/execution :: submit |
| src/spice/execution/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/execution/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/execution/models.py | replace | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/execution :: submit |
| src/spice/execution/provenance.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/execution :: submit |
| src/spice/execution/remote_runner.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/execution :: submit |
| src/spice/execution/session.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/execution :: submit |
| src/spice/execution/submission.py | replace | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/execution :: submit |
| src/spice/execution/transfer_transaction.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | src/spice/execution :: submit |
| src/spice/features/__init__.py :: CanonicalBlockSeries, CompiledFeatureContract, ResolvedFeatureTable, compile_feature_contract exports | replace | S05 — Construct and scale exact causal feature rows | src/spice/temporal/features.py |
| src/spice/features/__init__.py :: reader-only feature validation exports | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/__init__.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/features/contracts.py | replace | S05 — Construct and scale exact causal feature rows | src/spice/temporal/features.py |
| src/spice/features/core.py :: active compilation, table, and fingerprint surfaces | replace | S05 — Construct and scale exact causal feature rows | FeatureState, fit_feature_state, transform_feature_rows |
| src/spice/features/core.py :: reader-only feature semantics/catalog validation | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/core.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/registry.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/__init__.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/__init__.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/_base_fee.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/_block_facts.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/_family_builder.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/_fee_context.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/_priority_fee.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/_time.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/_transforms.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/elapsed_position.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/safe.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/features/sets/core_fee_dynamics/with_priority_fee.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/metrics.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/__init__.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: ArtifactAssociation, train, load_artifact |
| src/spice/modeling/_fit_policy.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/_runtime.py :: CudaModelingRuntime, seed/backend/precision/CUDA readiness/batch runtime helpers | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | Lightning native mechanics |
| src/spice/modeling/_runtime.py :: ForwardBatch and run_model_forward_pass | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | evaluate direct model invocation |
| src/spice/modeling/_runtime.py :: unqualified remainder | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | native Lightning train plus direct evaluate |
| src/spice/modeling/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/modeling/artifact_inference.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/modeling/artifacts.py :: LoadedTrainingArtifact, model.pt load/write, manifest builder, load_training_artifact, persist_training_artifact | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | ArtifactAssociation and native Lightning checkpoint |
| src/spice/modeling/artifacts.py :: unqualified remainder | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/batch_plan.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/dataset_builders/__init__.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/dataset_builders/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/modeling/dataset_builders/base.py :: sequence_runtime_metadata and validate_feature_prerequisites | replace | S08 — Prepare exact historical windows as lazy CPU datasets | HistoricalPreparation |
| src/spice/modeling/dataset_builders/base.py :: SequenceRuntimeMetadata reader DTO | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/dataset_builders/base.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/dataset_builders/fixed_sequence_temporal.py | replace | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/modeling/dataset_builders/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/modeling/dataset_builders/preparation.py | replace | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/modeling/families/__init__.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/families/_heads.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/families/_sequence.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/families/_transformer_shared.py :: legacy reader-only config values | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/families/_transformer_shared.py :: runtime position and encoder construction | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | S11 private Transformer construction |
| src/spice/modeling/families/_transformer_shared.py :: unqualified remainder | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/families/_transformer_shared.py :: value validation helpers | replace | S01 — Establish strict request/definition values and canonical direct addresses | exact Transformer and Transformer-LSTM value validation |
| src/spice/modeling/families/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/modeling/families/base.py :: model definition/capacity/method/method-space value surfaces | replace | S01 — Establish strict request/definition values and canonical direct addresses | three exact Definition, Capacity, Method, and MethodSpace branches |
| src/spice/modeling/families/base.py :: unqualified remainder | replace | S01 — Establish strict request/definition values and canonical direct addresses | src/spice/config :: exact Definition/Capacity/Method/MethodSpace values |
| src/spice/modeling/families/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/modeling/families/lstm.py :: legacy config, capacity, method, method-space value surfaces | replace | S01 — Establish strict request/definition values and canonical direct addresses | exact family-specific Definition, Capacity, Method, and MethodSpace |
| src/spice/modeling/families/lstm.py :: legacy reader-only model config values | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/families/lstm.py :: LSTMBaseline and _build_model | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | S11 LSTM FitModule construction |
| src/spice/modeling/families/lstm.py :: unqualified remainder | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/families/registry.py :: build_model | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | S11 private concrete model construction |
| src/spice/modeling/families/registry.py :: legacy reader-only config coercion | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/families/registry.py :: ModelSpec, _model_spec_loaders, model_spec, coerce_model_config, family MODEL_SPEC registrations | delete | S01 — Establish strict request/definition values and canonical direct addresses | direct discriminated family values |
| src/spice/modeling/families/registry.py :: unqualified remainder | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/families/transformer_lstm.py :: legacy config, capacity, method, method-space value surfaces | replace | S01 — Establish strict request/definition values and canonical direct addresses | exact family-specific Definition, Capacity, Method, and MethodSpace |
| src/spice/modeling/families/transformer_lstm.py :: legacy reader-only model config values | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/families/transformer_lstm.py :: TransformerLSTMBaseline and _build_model | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | S11 Transformer-LSTM FitModule construction |
| src/spice/modeling/families/transformer_lstm.py :: unqualified remainder | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/families/transformer.py :: legacy config, capacity, method, method-space value surfaces | replace | S01 — Establish strict request/definition values and canonical direct addresses | exact family-specific Definition, Capacity, Method, and MethodSpace |
| src/spice/modeling/families/transformer.py :: legacy reader-only model config values | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/families/transformer.py :: TransformerBaseline, _build_model, encoder execution | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | S11 Transformer FitModule construction |
| src/spice/modeling/families/transformer.py :: unqualified remainder | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/forward_runtime.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/modeling/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/modeling/lightning_module.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/models.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/persisted_training.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/pipeline.py :: TrainingSpec, TrainingRunCallbacks, build_artifact_training_spec, build_trial_training_spec, _build_training_spec, run_training, host preparation | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | train and run_candidate |
| src/spice/modeling/pipeline.py :: unqualified remainder | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/representations/__init__.py | replace | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/modeling/representations/sequence_inputs.py | replace | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/modeling/results.py :: active EvaluationSummary construction surfaces | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | evaluation.json and observations.parquet |
| src/spice/modeling/results.py :: active TrainingRunResult and build_training_runtime_summary | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | ArtifactAssociation and native checkpoint |
| src/spice/modeling/results.py :: legacy Training source/manifest/summary and Evaluation provenance/config/runtime/summary DTOs | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/results.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/runtime_planning.py :: build_cpu_modeling_runtime_plan | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | load_artifact native CPU/eval behavior |
| src/spice/modeling/runtime_planning.py :: Evaluate runtime-plan rows | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | load_artifact plus direct evaluation |
| src/spice/modeling/runtime_planning.py :: training and CUDA runtime-plan rows | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | Lightning native device/precision mechanics |
| src/spice/modeling/runtime_planning.py :: unqualified remainder | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | native owner-local runtime |
| src/spice/modeling/scoring.py | replace | S12 — Evaluate one native artifact over one historical window and publish canonical observations | src/spice/evaluation :: evaluate |
| src/spice/modeling/summary.py | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| src/spice/modeling/training_run.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/training_runner_types.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/training_runner.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/training_runtime.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | src/spice/modeling :: native Lightning train/load and three families |
| src/spice/modeling/tuned_config.py :: active sampling and parameter-application surfaces | replace | S09 — Publish immutable Studies and materialize selected training | apply_method and training_definition_from_method |
| src/spice/modeling/tuned_config.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/modeling/tuning_execution.py | replace | S13 — Run one typed Study candidate and retain its successful result | src/spice/tuning.py :: run_candidate |
| src/spice/modeling/tuning.py | replace | S09 — Publish immutable Studies and materialize selected training | src/spice/study :: Study and selected training |
| src/spice/prediction/__init__.py :: active task exports | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/__init__.py :: reader-only validate_prediction_family_id export shell | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/prediction/__init__.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/prediction/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/prediction/base.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/contracts.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/decoded_offsets.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/decoding.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/families/__init__.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/families/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/prediction/families/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/prediction/families/min_block_fee_multitask/__init__.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/families/min_block_fee_multitask/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/prediction/families/min_block_fee_multitask/batch.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/families/min_block_fee_multitask/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/prediction/families/min_block_fee_multitask/loss.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/families/min_block_fee_multitask/metrics.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/families/min_block_fee_multitask/outputs.py | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/registry.py :: _SUPPORTED_PREDICTION_FAMILY_IDS, _require_prediction_family_id, validate_prediction_family_id | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/prediction/registry.py :: active compile and dispatch surfaces | replace | S06 — Implement the architecture-neutral Min-Block-Fee task | src/spice/min_block_fee.py |
| src/spice/prediction/registry.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/semantics.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/serving/__init__.py | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/serving/analytics.py | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/serving/api.py | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/serving/config.py | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/serving/inference.py | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/serving/live_blocks.py | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/serving/runtime.py :: CORE_CORPUS_SOURCE_COLUMNS import and use | replace | S04 — Cut over native Corpus acquisition execution and CLI | private serving-local literal |
| src/spice/serving/runtime.py :: unqualified remainder | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/serving/schemas.py | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | src/spice/serving.py |
| src/spice/storage/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/storage/artifact_codecs.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/artifact_codecs.py :: writer-side evaluation encode rows | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | evaluation.json and observations.parquet |
| src/spice/storage/artifact.py :: evaluation summary writers and transaction mutation | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | evaluation directory direct publication |
| src/spice/storage/artifact.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/artifact.py :: write_artifact_manifest and write_training_summary | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | native checkpoint direct rename |
| src/spice/storage/catalog/__init__.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/catalog/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/storage/catalog/codecs.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/catalog/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/storage/catalog/index.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/catalog/materialization.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/catalog/records.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/catalog/registry.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/catalog/schema.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/catalog/store.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/corpus_codecs.py :: ACQUIRE_RUN_CODEC | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/storage/corpus_codecs.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/corpus.py :: _ACQUIRE_RUN_STORE, write_corpus_state, list_acquire_runs, _now_timestamp | delete | S04 — Cut over native Corpus acquisition execution and CLI | direct Corpus publication |
| src/spice/storage/corpus.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/engine.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/errors.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/identity.py :: generic identity records, payloads, content-derived IDs, association validators | replace | S01 — Establish strict request/definition values and canonical direct addresses | strict request/definition/source association |
| src/spice/storage/identity.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/ids.py :: _stable_id, _canonical_identity, study_storage_id, artifact_storage_id | replace | S01 — Establish strict request/definition values and canonical direct addresses | four request-specific UUIDv4 mint constructors |
| src/spice/storage/ids.py :: corpus_storage_id | delete | S04 — Cut over native Corpus acquisition execution and CLI | CorpusRequest UUID |
| src/spice/storage/ids.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/storage/inspect_artifact.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/inspect_dataset.py :: acquire-run load, fields, rendering, acquire_run_string | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/storage/inspect_dataset.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/inspect_study.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/inspect.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/layout.py :: artifact_root_path | replace | S01 — Establish strict request/definition values and canonical direct addresses | artifacts/<artifact_id>.ckpt |
| src/spice/storage/layout.py :: corpus_blocks_dir_path | replace | S01 — Establish strict request/definition values and canonical direct addresses | corpora/<corpus_id>/blocks.parquet |
| src/spice/storage/layout.py :: corpus_root_path | replace | S01 — Establish strict request/definition values and canonical direct addresses | exact Corpus directory address from explicit STORAGE_ROOT and corpus UUID |
| src/spice/storage/layout.py :: study_root_path | replace | S01 — Establish strict request/definition values and canonical direct addresses | studies/<study_id>.json |
| src/spice/storage/layout.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/lifecycle.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/operator.py :: DatasetInspectionDetail.RUNS and Corpus detail registration | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/storage/operator.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/payloads.py :: SequencePayloadStore | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/storage/payloads.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/schema.py :: acquire_runs and DATASET_TABLES membership | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/storage/schema.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/selectors.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/semantics_codecs.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/study_manifest_codecs.py :: active encode/from-Study-manifest writer surfaces | delete | S09 — Publish immutable Studies and materialize selected training | Study JSON model_dump_json |
| src/spice/storage/study_manifest_codecs.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/study_manifest.py :: active manifest construction, insertion, diff, validation, and writer surfaces | replace | S09 — Publish immutable Studies and materialize selected training | src/spice/study :: publish_study and retain_result |
| src/spice/storage/study_manifest.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/study_models.py :: active stored-summary, best-selection, sampler, pruner, and trial-summary construction | replace | S09 — Publish immutable Studies and materialize selected training | Study and RetainedResult |
| src/spice/storage/study_models.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/study_optuna.py :: active writer/create/best-selection/general helper surfaces | delete | S09 — Publish immutable Studies and materialize selected training | direct Study JSON |
| src/spice/storage/study_optuna.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/study_render.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/sync_cli.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/transactions.py :: commit_corpus_acquisition | delete | S04 — Cut over native Corpus acquisition execution and CLI | direct Corpus publication |
| src/spice/storage/transactions.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/workflow_root_materialization.py :: produced_corpus_id, materialize_acquire_roots, Acquire arms, ProducedRootFacts.corpus_id | delete | S04 — Cut over native Corpus acquisition execution and CLI | direct Corpus address |
| src/spice/storage/workflow_root_materialization.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/storage/workflow_roots.py :: AcquireWorkflowRoots and produced_corpus_root_handle | delete | S04 — Cut over native Corpus acquisition execution and CLI | direct Corpus address |
| src/spice/storage/workflow_roots.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/__init__.py :: active execution-policy imports and exports | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | direct h + 1 + k |
| src/spice/temporal/__init__.py :: unqualified remainder | replace | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal :: history/features exports |
| src/spice/temporal/ARCHITECTURE.md | replace | S24 — Reconcile final normative documentation and tracked repository hygiene | src/fable/temporal/ARCHITECTURE.md |
| src/spice/temporal/capability.py :: active capability construction | replace | S08 — Prepare exact historical windows as lazy CPU datasets | HistoricalPreparation |
| src/spice/temporal/capability.py :: legacy TemporalCapability reader DTO | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/capability.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/compilers/__init__.py :: active compiler exports | delete | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/temporal/compilers/__init__.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/compilers/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/temporal/compilers/base.py :: active compiler runtime | delete | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/temporal/compilers/base.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/compilers/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/temporal/compilers/observed_time_window.py :: active observed-time compiler runtime | delete | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/temporal/compilers/observed_time_window.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/compilers/registry.py :: active compiler registry | delete | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/temporal/compilers/registry.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/contracts.py :: active historical compiler contract construction | replace | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/temporal/contracts.py :: legacy config-only compiler DTOs | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/contracts.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/execution_policy/__init__.py :: active runtime exports | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | direct h + 1 + k |
| src/spice/temporal/execution_policy/__init__.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/execution_policy/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/temporal/execution_policy/base.py :: ExecutionPolicyConfig, StrictDeadlineMissConfig, supported-ID validation/coercion | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/execution_policy/base.py :: PreparedActionSpace, PreparedTemporalOutcomeFacts, PreparedTemporalFacts, RealizedSelectionBatch, DecodedOffsetBatch, callback aliases, CompiledExecutionPolicyContract, runtime preparation/realization/compiler functions | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | direct S05/S06 request path and h + 1 + k |
| src/spice/temporal/execution_policy/base.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/execution_policy/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/temporal/execution_policy/strict_deadline_miss.py :: active runtime policy implementation | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | direct h + 1 + k |
| src/spice/temporal/execution_policy/strict_deadline_miss.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/input_normalization/__init__.py :: active scaler operation exports | replace | S05 — Construct and scale exact causal feature rows | src/spice/temporal/features.py |
| src/spice/temporal/input_normalization/__init__.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/input_normalization/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/temporal/input_normalization/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/temporal/input_normalization/scaling.py :: fit_row_standard_scaler, transform_feature_matrix, transform_problem_store_features | replace | S05 — Construct and scale exact causal feature rows | FeatureState, fit_feature_state, transform_feature_rows |
| src/spice/temporal/input_normalization/scaling.py :: ScalerStats reader DTO | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/input_normalization/scaling.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/problem_store.py :: active CompiledProblemStore runtime | replace | S08 — Prepare exact historical windows as lazy CPU datasets | src/spice/temporal/history.py |
| src/spice/temporal/problem_store.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/semantics.py :: active temporal semantics construction | replace | S08 — Prepare exact historical windows as lazy CPU datasets | ExperimentSemantics |
| src/spice/temporal/semantics.py :: legacy temporal semantic reader DTOs | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/temporal/semantics.py :: unqualified remainder | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| src/spice/workflows/__init__.py | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| src/spice/workflows/acquire.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | src/spice/acquisition :: acquire_corpus |
| src/spice/workflows/ARCHITECTURE.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/workflows/evaluate.py | delete | S17 — Execute one typed Train or Evaluate request on the hidden remote worker | src/spice/cli/commands/remote.py :: hidden workflow |
| src/spice/workflows/IMPLEMENTATIONS.md | delete | S24 — Reconcile final normative documentation and tracked repository hygiene | — |
| src/spice/workflows/preparation.py :: PreparedAcquireWorkflow and prepare_acquire | delete | S04 — Cut over native Corpus acquisition execution and CLI | acquire_corpus |
| src/spice/workflows/preparation.py :: PreparedTrainWorkflow, PreparedEvaluateWorkflow, prepare_train, prepare_evaluate, _active_train_config, Train/Evaluate-only imports | delete | S17 — Execute one typed Train or Evaluate request on the hidden remote worker | src/spice/cli/commands/remote.py :: hidden workflow |
| src/spice/workflows/preparation.py :: PreparedTuneWorkflow, prepare_tune, _build_tuning_coverage_spec, _validate_training_coverage, Tune-only imports | delete | S19 — Submit one Study candidate and finalize the current Study | src/spice/cli/commands/study.py :: study run |
| src/spice/workflows/preparation.py :: unqualified remainder | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| src/spice/workflows/reporting.py :: acquire_workflow_facts, report_acquire_result, report_acquire_staging_warning | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| src/spice/workflows/reporting.py :: Train/Evaluate facts, callbacks, results, _evaluation_result_fields, _fit_epoch_message, Train/Evaluate-only imports | delete | S17 — Execute one typed Train or Evaluate request on the hidden remote worker | src/spice/cli/commands/remote.py :: hidden workflow |
| src/spice/workflows/reporting.py :: Tune imports, tune_workflow_facts, report_tune_resume, report_tune_study_start, report_tune_trial, report_tune_best, report_tune_result, tune_reporting_callbacks, _trial_message | delete | S19 — Submit one Study candidate and finalize the current Study | src/spice/cli/commands/study.py :: study run |
| src/spice/workflows/reporting.py :: unqualified remainder | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| src/spice/workflows/train.py | delete | S17 — Execute one typed Train or Evaluate request on the hidden remote worker | src/spice/cli/commands/remote.py :: hidden workflow |
| src/spice/workflows/tune.py | delete | S19 — Submit one Study candidate and finalize the current Study | src/spice/cli/commands/study.py and hidden remote candidate |
| surface :: ASGI export :: spice.serving:app | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | spice.serving:create_app |
| surface :: CLI command :: spice acquire | replace | S04 — Cut over native Corpus acquisition execution and CLI | spice corpus acquire REQUEST.json --rpc-url URL |
| surface :: CLI command :: spice config edit provider NAME | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| surface :: CLI command :: spice config list provider | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| surface :: CLI command :: spice config show provider NAME | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| surface :: CLI command :: spice evaluate | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | spice submit REQUEST.json |
| surface :: CLI command :: spice train | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | spice submit REQUEST.json |
| surface :: CLI command :: spice tune | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | spice study run TUNE_REQUEST.json METHOD.json |
| surface :: CLI command group :: spice benchmark | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| surface :: CLI command group :: spice config | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request files and REMOTE.yaml |
| surface :: CLI command group :: spice delete | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| surface :: CLI command group :: spice refresh | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| surface :: CLI command group :: spice show | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| surface :: CLI command group :: spice transfer | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | external rsync/scp |
| surface :: CLI option :: spice show corpus --detail runs | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| surface :: CLI root :: spice | replace | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | plain Typer root with submit, corpus, study, and hidden remote leaves |
| surface :: config group :: BENCHMARK | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | src/spice/protocol.py |
| surface :: config group :: CHAIN | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | three neutral RPC URL variables and direct numeric chain checks |
| surface :: config group :: CORPUS | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | CorpusRequest JSON |
| surface :: config group :: EVALUATIONS | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | EvaluateRequest lists |
| surface :: config group :: EVALUATOR | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | EvaluationRequest |
| surface :: config group :: EXECUTION | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | cwd-local REMOTE.yaml |
| surface :: config group :: MODEL | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | Definition and Method |
| surface :: config group :: PREDICTION | delete | S06 — Implement the architecture-neutral Min-Block-Fee task | ExperimentSemantics |
| surface :: config group :: PROBLEM | delete | S08 — Prepare exact historical windows as lazy CPU datasets | ExperimentSemantics |
| surface :: config group :: SPLIT | delete | S08 — Prepare exact historical windows as lazy CPU datasets | TrainRequest and fixed role geometry |
| surface :: config group :: SURFACE | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | strict request JSON |
| surface :: config group :: TRAINING | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | TrainingDefinition |
| surface :: config group :: TUNING | delete | S09 — Publish immutable Studies and materialize selected training | TuneRequest |
| surface :: config group :: TUNING_SPACE | delete | S09 — Publish immutable Studies and materialize selected training | MethodSpace |
| surface :: console entry :: spice = spice.cli.app:main | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | fable = fable.cli.app:main |
| surface :: direct dependency :: aiohttp | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | resolver-owned transitive only |
| surface :: direct dependency :: eth-typing | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | resolver-owned transitive only |
| surface :: direct dependency :: optuna | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| surface :: direct dependency :: scikit-learn | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| surface :: direct dependency :: sqlalchemy | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | — |
| surface :: direct dependency :: uvicorn[standard] | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | uvicorn |
| surface :: direct dependency :: websockets | delete | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | resolver-owned transitive only |
| surface :: environment :: EXPO_PUBLIC_SPICE_BACKEND_URL | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | EXPO_PUBLIC_FABLE_BACKEND_URL |
| surface :: environment :: SPICE_SERVING_ANALYTICS_DB | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| surface :: environment :: SPICE_SERVING_ARTIFACT_CHAIN_NAME | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | request.chain plus artifact association |
| surface :: environment :: SPICE_SERVING_ARTIFACT_ID | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | private 12-entry literal map |
| surface :: environment :: SPICE_SERVING_CHAIN_NAME | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | request.chain |
| surface :: environment :: SPICE_SERVING_CONFIRMATION_DEPTH | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| surface :: environment :: SPICE_SERVING_DEMO_CONTRACT_ADDRESS | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| surface :: environment :: SPICE_SERVING_RPC_URL | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | ETHEREUM_RPC_URL, POLYGON_RPC_URL, AVALANCHE_RPC_URL |
| surface :: environment :: SPICE_SERVING_STORAGE_ROOT | replace | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | STORAGE_ROOT |
| surface :: Expo display identity :: current SPICE/Sepolia manifest identity | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | FABLE Demo / fable-demo / dev.edoski.fable.demo |
| surface :: HTTP route :: GET /health | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| surface :: HTTP route :: GET /v1/analytics | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| surface :: HTTP route :: GET /v1/model | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | POST /inference |
| surface :: HTTP route :: POST /v1/predictions | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | POST /inference |
| surface :: HTTP route :: POST /v1/transactions/{request_id}/observe | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| surface :: npm package identity :: current mobile package | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | fable-mobile-demo 0.1.0 |
| surface :: Python distribution :: spice | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | fable 0.1.0 |
| surface :: Python import root :: spice | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | fable |
| surface :: Python package API :: spice.execution | replace | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | from spice.execution import submit |
| surface :: Uvicorn factory :: spice.serving:create_app | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | fable.serving:create_app |
| surface :: wheel package selection :: recursive src/spice plus package YAML/Markdown | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | src/fable/**/*.py only |
| tests/__init__.py | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | tests/__init__.py :: FABLE test-package identity |
| tests/acquisition/test_pull.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| tests/acquisition/test_rpc_client.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/artifact_helpers.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/benchmarks/test_benchmarks.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| tests/benchmarks/test_collection_resolver.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| tests/benchmarks/test_collection.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| tests/benchmarks/test_plan_materialization.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| tests/benchmarks/test_result_index.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| tests/benchmarks/test_run_state_codec.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/benchmarks/test_window_suite_writer.py | delete | S10 — Construct and select the twelve-list temporal-baseline protocol | — |
| tests/catalog_helpers.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/cli/test_benchmark_cli.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/cli/test_config_cli.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/cli/test_storage_cli.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/cli/test_transfer_cli.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/config/test_groups.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/config/test_resolution.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/config/test_selections.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/config/test_workflow_snapshots.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/conftest.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/core/test_async_runtime.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| tests/core/test_console.py | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| tests/corpus/test_assembly.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| tests/corpus/test_contract.py | replace | S02 — Load and validate one canonical Corpus | focused S02 Corpus loader/schema test |
| tests/corpus/test_corpus_planning.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| tests/corpus/test_coverage.py | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| tests/corpus/test_metadata.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/corpus/test_split_materialization.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| tests/corpus/test_validation.py | replace | S02 — Load and validate one canonical Corpus | focused S02 Corpus loader/schema test |
| tests/dataset_helpers.py | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| tests/evaluation/test_evaluators.py | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | — |
| tests/evaluation/test_temporal_accounting.py | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | — |
| tests/evaluation/test_temporal_replay.py | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | — |
| tests/execution/test_session.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/execution/test_submission.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/execution/test_transfer.py | delete | S07 — Submit one typed workflow through SSH/Slurm and cut over the CLI root | — |
| tests/features/test_core_fee_dynamics.py | delete | S05 — Construct and scale exact causal feature rows | — |
| tests/modeling/test_artifact_inference.py | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | — |
| tests/modeling/test_batch_plan.py | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| tests/modeling/test_dataset_builders.py | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| tests/modeling/test_fit_policy.py | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| tests/modeling/test_forward_runtime.py | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | — |
| tests/modeling/test_models.py | replace | S11 — Fit the three concrete models and publish native Lightning artifacts | focused S11 native train/load test |
| tests/modeling/test_persisted_training.py | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| tests/modeling/test_representations.py | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| tests/modeling/test_runtime.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/modeling/test_scoring.py | delete | S12 — Evaluate one native artifact over one historical window and publish canonical observations | — |
| tests/modeling/test_training_runner.py | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| tests/modeling/test_training_runtime.py | delete | S11 — Fit the three concrete models and publish native Lightning artifacts | — |
| tests/modeling/test_tuned_config.py | delete | S09 — Publish immutable Studies and materialize selected training | — |
| tests/modeling/test_tuning_execution.py | delete | S13 — Run one typed Study candidate and retain its successful result | — |
| tests/prediction/test_decoded_offsets.py | delete | S06 — Implement the architecture-neutral Min-Block-Fee task | — |
| tests/prediction/test_min_block_fee_multitask.py | delete | S06 — Implement the architecture-neutral Min-Block-Fee task | — |
| tests/root_handle_helpers.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/serving/test_analytics.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/serving/test_api.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/serving/test_inference.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/serving/test_live_blocks.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/serving/test_serving_runtime.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/storage/test_artifact.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_catalog_codecs.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_catalog.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_identity.py | replace | S01 — Establish strict request/definition values and canonical direct addresses | focused S01 identity/address test |
| tests/storage/test_inspect_artifact.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_operator.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_read_only_loads.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_roots.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_staging.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_study_manifest.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_sync_cli.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/storage/test_workflow_roots.py | delete | S22 — Delete the behavior-free legacy persisted-reader closure after accepted Issue #12 export | — |
| tests/temporal/test_execution_policy_contract.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/temporal/test_input_normalization.py | delete | S05 — Construct and scale exact causal feature rows | — |
| tests/temporal/test_observed_time_window.py | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| tests/temporal/test_problem_store.py | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| tests/temporal/test_realization.py | delete | S20 — Serve the exact final-K artifacts through one stateless Mac inference API | — |
| tests/temporal/test_temporal_capability.py | delete | S08 — Prepare exact historical windows as lazy CPU datasets | — |
| tests/workflows/test_acquire.py | delete | S04 — Cut over native Corpus acquisition execution and CLI | — |
| tests/workflows/test_preparation.py :: Train/Evaluate tests, fixtures, helpers, imports | delete | S17 — Execute one typed Train or Evaluate request on the hidden remote worker | — |
| tests/workflows/test_preparation.py :: Tune tests, fixtures, helpers, imports | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| tests/workflows/test_preparation.py :: unqualified remainder | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| tests/workflows/test_reporting.py :: Train/Evaluate tests, fixtures, helpers, imports | delete | S17 — Execute one typed Train or Evaluate request on the hidden remote worker | — |
| tests/workflows/test_reporting.py :: Tune tests, fixtures, helpers, imports | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| tests/workflows/test_reporting.py :: unqualified remainder | delete | S19 — Submit one Study candidate and finalize the current Study | — |
| uv.lock | replace | S23 — Cut the surviving FABLE identity, packages, and dependencies atomically | uv.lock |

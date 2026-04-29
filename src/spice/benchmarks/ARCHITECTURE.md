# Benchmark Architecture

## Purpose

`benchmarks` owns checked-in benchmark specs, workflow-selection expansion, dependency-aware plan compilation, remote submission orchestration, collection, and ledger projection.

The benchmark domain should not live under config. It uses config resolution, but its own concepts are benchmark cases, steps, runs, submissions, collections, and result rows.

## Flow

```text
benchmark YAML spec
    |
    v
BenchmarkSpec
    |
    v
expanded Benchmark Workflow Selections
    |
    v
resolve_workflow_config()
    |
    v
BenchmarkPlanEntry JSONL
    |
    v
submit / collect / ledger
```

Planning builds typed workflow selections and calls normal workflow resolution. Inline problem grids produce inline `ProblemSpec` values during planning; plan JSON stores the selected problem id, while the resolved workflow config stores the full executable problem.

## Module Map

```text
benchmarks/
  schema.py      benchmark YAML schema
  planning.py    dimension expansion and workflow-selection rows
  __init__.py    plan compilation API
  runs.py        run-state files and JSONL codecs
  submission.py  remote workflow submission service
  collection_resolver.py  remote evaluate-result resolver
  collection.py  remote result collection service
  ledger.py      result CSV projection
```

## Boundaries

The CLI only renders plan, submission, and collection JSONL. It does not coordinate benchmark DAGs or storage pulls.

Remote transfer during collection goes through a **Benchmark Collection Resolver** using an **Execution Session** and `execution.transfer`. Storage selectors identify existing study/artifact roots; storage lifecycle performs local root validation and promotion.

Benchmark JSON shapes are operator-facing. Keep them stable unless a field name is part of a deliberate terminology cleanup.

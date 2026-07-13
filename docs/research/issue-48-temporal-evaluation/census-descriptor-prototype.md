# Full-census descriptor prototype

Status: throwaway Issue-48 logic prototype. It changes no production code, corpus,
artifact, database, configuration, or remote state.

Question: can direct parent-fee and one-block-change descriptions use every eligible
origin without selecting evaluation windows?

Run the fixed demonstration:

```sh
uv run python docs/research/issue-48-temporal-evaluation/explore_census_descriptors.py --demo
```

Omit `--demo` for the small interactive terminal view.

The fixture compares four constructions over the same raw origin accounting:

1. the full census;
2. predeclared value-quartile bins of a causal per-origin descriptor, retaining every origin;
3. low/high representative contiguous windows, which retain only a subset;
4. a deliberately invalid outcome-picked subset.

The descriptor bins recombine to the exact full-census numerators and denominator. They
are presentation strata, not a new estimand or sample. Representative windows do not
recombine because they change the evaluated population. Choosing them only from x-values
can be a legitimate designed-stratum study if frozen in advance, but it is unnecessary
for the approved exhaustive headline; changing their rule after viewing economic y-values
would be outcome-informed selection.

The two descriptors are direct facts known at origin `h`: raw
`base_fee_per_gas[h]` of the latest closed parent, and signed
`log(base_fee[h]/base_fee[h-1])`. The second is one-step direction and magnitude, not
volatility. Neither needs visible-context `C`, a rolling width, or an evaluation-window
duration. Neither uses the immediate target `h+1` or any selected/hindsight target fee.

The prototype uses nearest-rank empirical quartile cutpoints. Equal descriptor values are
never split to force equal counts, so bins may be unequal or empty. Every origin still
appears once and the four bins must recombine to the full raw accounting exactly.

Prototype verdict: fixed contiguous evaluation windows are unnecessary for direct
fee/change plots. Use every origin, the two one-block descriptors, and—only for readable
aggregation—a frozen all-origin quartile rule with visible counts and boundaries. Display
the skewed raw-fee x-axis logarithmically, but keep raw fee values as the descriptor and
for cutpoints.

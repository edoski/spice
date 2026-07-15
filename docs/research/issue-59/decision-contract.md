# Issue 59: FABLE naming and SPICE attribution decision contract

Date: 2026-07-15

Status: approved by Edo on 2026-07-15. Approval authorizes only ticket-scoped research
publication, one Resolution and closure on Issue 59, one Wayfinder pointer, and
verification. It does not authorize repository renaming or implementation mutation.

## Canonical human identity

- The project and thesis system are **FABLE — Fee Analysis through Blockchain Learning and
  Estimation**.
- Every document expands the first substantive system mention as **FABLE (Fee Analysis
  through Blockchain Learning and Estimation)**, then uses **FABLE**. Title-case **Fable**
  is not a second display form.
- The mobile and serving displays are **FABLE Demo** and **FABLE Inference API**.
- A later thesis title or subtitle may frame the work, but it must use FABLE consistently
  and cannot reopen the system name.

## Unified active technical identity

The single active stem is `fable`. On final surviving identity seams it means:

- GitHub repository `edoski/fable`;
- Python distribution, import package, installed executable, and hidden remote leaves
  `fable`;
- operator-facing **FABLE** job and log labels and any surviving project-owned environment
  prefix `FABLE_`;
- private mobile package `fable-mobile-demo`, Expo slug and scheme `fable-demo`, and bundle
  identifier `dev.edoski.fable.demo`;
- **FABLE** in active documentation, thesis prose, report and figure titles, and serving UI.

These mappings apply only to final survivors through their later specification,
implementation, and cutover tickets. Issue 59 performs none of those mutations.

## Neutral domain and durable identity

- Corpus, study, artifact, and evaluation IDs remain unbranded UUIDs at exact typed
  addresses. Their schemas contain no FABLE branding field.
- Internal types use responsibility names such as `OperatorError`; branding is not copied
  mechanically into domain names.
- Filenames and report columns remain descriptive and gain no mandatory `fable_` prefix.
- Obsolete `.spice`, `spice_meta`, serving SQLite, wallet key, Python remote launcher, and
  `SpiceDemo` surfaces are deleted by their owning implementation tickets, not translated
  into FABLE equivalents.
- There are no CLI or import aliases, environment fallbacks, dual URL schemes, legacy
  readers, migration shims, or compatibility tests.

## SPICE attribution boundary

**SPICE** names only the complete spatial, temporal, and distributed-reputation framework
described in *SPICE: A Predictive Framework for Cost-Optimization in Multichain
Environments*. FABLE is classified as derived from and extending selected temporal work,
not as SPICE, a SPICE reproduction, or a reproduction of its temporal module.

The canonical attribution paragraph is:

> FABLE is a clean-break temporal fee-analysis system derived from and extending the
> temporal optimization component described in *SPICE: A Predictive Framework for
> Cost-Optimization in Multichain Environments*. It reimplements selected experimental
> elements—the two-head minimum-block task and the LSTM, Transformer, and
> Transformer-LSTM comparison lineage—while defining its own closed-parent fixed-K
> decision contract, causal preprocessing, selection, evaluation, persistence, CLI, and
> inference serving. FABLE is not a reproduction of SPICE and does not implement SPICE's
> spatial-routing or distributed-reputation modules.

The final bibliography supplies authors only from an accepted non-anonymous bibliographic
source. Commit identity is not author evidence, and exact numerical reproduction is not
claimed.

## Clean-break vocabulary and history

Active normative prose distinguishes **paper fact**, **FABLE lineage**, **FABLE-owned
design or extension**, and **historical SPICE evidence**. It does not say “current SPICE,”
call FABLE a “SPICE implementation,” use unqualified “SPICE extension,” claim “SPICE
reproduction,” combine the names as “SPICE/FABLE,” or call FABLE “formerly SPICE.”

Old research, reports, paths, commands, Git history, and issue history retain `SPICE` or
`spice` verbatim when preserving evidence. Active prose labels quoted material historical.
History is not rewritten, migrated, or aliased. Map #1 receives one final pointer to this
decision instead of a broad rewrite of historical planning comments.

## Ticket boundary and approval gate

Issue 59 freezes terminology and attribution only. It does not rename or mutate code,
configuration, tests, data, storage, acquisition, training, evaluation, jobs, archives,
mobile artifacts, or repository settings. Later owning tickets specify and execute the
clean break. Previously reviewed name collisions and a hypothetical future public registry
release do not reopen the chosen identity automatically.

Edo's explicit approval of this complete contract authorizes only ticket-scoped research
publication, a Resolution and closure on Issue 59, one Wayfinder pointer on map #1, and
verification. It does not authorize implementation or real execution.

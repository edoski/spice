# Issue 47: three-role split theory

**Status:** bounded planning evidence. No owner decision is recorded here.

**Question:** Does SPICE need a distinct internal-test role in addition to training,
validation, and sealed testing?

## Verdict

No. Exactly three roles are sufficient for this bounded thesis:

1. **Training** owns gradients and every fitted or data-dependent statistic.
2. **Validation** owns every development choice, including feature groups,
   context, scaling, HPO, checkpointing, training budget, metrics, and any
   predeclared comparison across validation windows.
3. **Testing** evaluates the one fully frozen development procedure once
   across its predeclared named reporting windows.

This is an inference from the sources below, not a theorem that prescribes SPICE's
role names. Standard guidance already uses train for fitting, validation for model
selection, and a held-out test for final evaluation; it does not require a fourth
role ([scikit-learn model-evaluation guide](https://scikit-learn.org/stable/modules/cross_validation.html)).
Primary empirical work requires performance evaluation to be outside the complete
training-plus-model-selection procedure, but does not require two successive test
sets ([Cawley and Talbot, 2010](https://www.jmlr.org/papers/v11/cawley10a.html);
[Reunanen, 2003](https://www.jmlr.org/papers/v3/reunanen03a.html)). Sealed testing
supplies that outside evaluation. It may contain multiple broad, predeclared
reporting windows; that does not create another development role.

## What is and is not lost

Removing internal test loses one convenience: a separately held-out rehearsal can
warn that development overfit validation before final testing is opened.
It loses no essential causal-leakage protection. Complete-outcome purging,
training-only fitted state, causal feature availability, and testing seals provide that
protection independently of how many holdouts are named.

It also loses no unique statistical role:

- If an internal-test result changes a feature, model, budget, period, metric, or
  claim, the period has participated in selection and is therefore validation.
- If it cannot change anything, it is another final test. Sealed testing
  already serves that role.

Repeatedly optimizing a finite validation criterion can overfit that criterion and
make its reported performance optimistic. This is **adaptive model-selection
overfitting**, not forward-target leakage: validation outcomes do not enter gradients
or fitted transforms, but they influence which candidate survives. Cawley and Talbot
show that this selection effect can be material even with few hyperparameters, and
Dwork et al. show more generally that adaptive reuse of a holdout can overfit the
holdout ([Cawley and Talbot, 2010](https://www.jmlr.org/papers/v11/cawley10a.html);
[Dwork et al., 2015](https://papers.nips.cc/paper_files/paper/2015/hash/bad5f33780c42f2588878a9d07405083-Abstract.html)).
A second holdout does not erase that effect; it only reveals it while it remains
unseen. Chronologically later testing gives a check of the resulting fixed procedure.
If an opened test result later guides development, that creates selection bias rather
than fitting leakage. The canonical Issue 48 contract retains and reports the range,
allows correctness/reproducibility reruns, and requires the iterative limitation to
be disclosed in plain prose; it adds no replacement-data state machine.

Multiple predeclared validation windows can reduce dependence on one arbitrary
temporal episode and expose instability, consistent with rolling-origin and
multiple-period forecast evaluation ([Tashman, 2000](https://doi.org/10.1016/S0169-2070(00)00065-0)).
Because all their results guide development, all remain validation. They do not turn
the validation score into a final performance estimate and do not broaden a final
claim beyond the testing chains, regimes, and periods actually evaluated.

## Required safeguards

The three-role contract is defensible only if all of these hold:

- Predeclare validation windows, metrics, aggregation/comparison rules, candidate
  families, and practical-equivalence rule. Log every validation-informed choice.
- Fit scalers, target transforms, class weights, learned representations, and model
  parameters on training only. Freeze them for validation and testing; do not
  refit on either held-out role in the baseline.
- Apply the approved complete-outcome rule at training-to-validation and
  validation-to-testing boundaries. Causal past context may overlap; forward
  outcomes may not.
- Before opening test results, freeze the exact code/protocol, feature set,
  context, scaler, HPO result, checkpoint, seeds and compute budget, periods,
  metrics, comparison rule, and intended claims. The evaluation path must not emit
  test metrics during development or HPO.
- Testing reports rather than selects. Correctness and reproducibility reruns on the
  same valuable range are allowed. Any later test-guided development is disclosed as
  a thesis selection-bias limitation under the canonical Issue 48 resolution, not
  encoded as discard or replacement-data state.
- Use deterministic fixtures and invariant checks for causal geometry, availability,
  purging, scaler ownership, and offline/live parity. Such checks replace a
  correctness-audit use of internal test; they do not estimate generalization.
- Scope conclusions to the observed testing chain/regime/period. Adjacent temporal
  origins overlap and are not an IID sample merely because there are many rows.

## Lean consequence

Delete the internal-test role rather than retaining a dormant option. This removes
one role cutoff, one purging transition, one prepared split, one metrics branch, and
the temptation to inspect a nominal test during each HPO trial. It also preserves
more scarce later Ethereum and Polygon history for the genuinely untouched testing
tail. Validation audits and deterministic fixtures cover development and correctness;
the sealed testing role alone covers final empirical assessment across its
predeclared named reporting windows.

## Corrected recommendation

Adopt the three-role contract exactly as stated above. There is no primary-source
theory or causal-safety contradiction. A fourth internal-test role would buy an
extra rehearsal, not an essential protection, and does not earn its data and code
cost for this thesis.

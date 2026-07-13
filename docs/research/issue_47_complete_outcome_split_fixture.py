"""THROWAWAY issue-47 fixture for complete-outcome role purging.

The numbers are deliberately tiny and illustrative.  ``K=2`` is not a
production action-width decision, and ``C=5`` is not a production context
decision.  The fixture proves one rule:

    an earlier role may keep origin h only when h + K < next_role_start

Past contexts may overlap across roles because they contain already available
history.  Fitted statistics still use only unique feature rows covered by fit
contexts.

Run with:

    uv run python docs/research/issue_47_complete_outcome_split_fixture.py
"""

from __future__ import annotations

from dataclasses import dataclass

CONTEXT_LENGTH = 5
ACTION_WIDTH = 2
FEATURE_WARMUP_ROWS = 1
REGIME_START_BLOCK = 0
TEST_AND_REGIME_END_BLOCK = 20


@dataclass(frozen=True)
class Role:
    name: str
    origin_start: int
    origin_stop: int
    next_role_start: int | None


ROLES = (
    Role("training", 5, 9, 9),
    Role("validation", 9, 13, 13),
    Role("testing", 13, 19, None),
)


def context_rows(origin: int) -> tuple[int, ...]:
    return tuple(range(origin - CONTEXT_LENGTH + 1, origin + 1))


def outcome_rows(origin: int) -> tuple[int, ...]:
    return tuple(range(origin + 1, origin + ACTION_WIDTH + 1))


def kept_origins(role: Role) -> tuple[int, ...]:
    candidates = range(role.origin_start, role.origin_stop)
    if role.next_role_start is None:
        return tuple(
            origin for origin in candidates if outcome_rows(origin)[-1] <= TEST_AND_REGIME_END_BLOCK
        )
    return tuple(origin for origin in candidates if outcome_rows(origin)[-1] < role.next_role_start)


def main() -> None:
    kept = {role.name: kept_origins(role) for role in ROLES}

    for role in ROLES:
        origins = kept[role.name]
        assert origins
        for origin in origins:
            dependency_start = context_rows(origin)[0] - FEATURE_WARMUP_ROWS
            assert dependency_start >= REGIME_START_BLOCK
            assert outcome_rows(origin)[-1] <= TEST_AND_REGIME_END_BLOCK
            if role.next_role_start is not None:
                assert outcome_rows(origin)[-1] < role.next_role_start
        purged = tuple(
            origin for origin in range(role.origin_start, role.origin_stop) if origin not in origins
        )
        print(
            f"{role.name:13} kept={origins} purged={purged} "
            f"first_context={context_rows(origins[0])} "
            f"last_outcomes={outcome_rows(origins[-1])}"
        )

    for earlier, later in zip(ROLES[:-1], ROLES[1:], strict=True):
        earlier_last = kept[earlier.name][-1]
        later_first = kept[later.name][0]
        shared_past = set(context_rows(earlier_last)) & set(context_rows(later_first))
        assert shared_past
        assert max(outcome_rows(earlier_last)) < later_first
        print(
            f"{earlier.name}->{later.name}: shared causal context="
            f"{tuple(sorted(shared_past))}; earlier outcomes="
            f"{outcome_rows(earlier_last)}; later starts={later_first}"
        )

    training_feature_rows = sorted(
        {row for origin in kept["training"] for row in context_rows(origin)}
    )
    validation_feature_rows = sorted(
        {row for origin in kept["validation"] for row in context_rows(origin)}
    )
    assert training_feature_rows == [1, 2, 3, 4, 5, 6]
    assert set(validation_feature_rows) - set(training_feature_rows) == {7, 8, 9, 10}
    print(f"fitted-label origins={kept['training']}")
    print(f"fitted-statistic rows={tuple(training_feature_rows)}")
    print(
        "validation-only rows excluded from fitted statistics="
        f"{tuple(sorted(set(validation_feature_rows) - set(training_feature_rows)))}"
    )


if __name__ == "__main__":
    main()

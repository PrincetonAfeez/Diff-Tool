# ADR 0006: Display Text and Word-Diff Policy

## Decision

Formatters render the edit script produced by the engine. For `EQUAL` rows,
display text comes from the old side (`old_text`). Word diff pairs consecutive
delete/insert blocks line-by-line and rejoins tokens with a single space.

## Rationale

Comparison flags such as `--ignore-case` and `--ignore-trailing-space` can make
lines equal while preserving different originals in the `Edit` model. Showing
`old_text` for matching rows keeps CLI output stable and avoids false visual
differences in side-by-side view.

Word diff is an optional presentation layer on top of line-level LCS. Pairing
within delete/insert blocks keeps the feature predictable without introducing a
`REPLACE` operation (see ADR 0002).

## Rules

1. **Unified / inline / side-by-side** iterate `result.edits`, not raw inputs.
2. **`EQUAL` rows** use `old_text` in formatters (library callers still have
   both sides on the `Edit`).
3. **`--ignore-blank-lines`** removes blank lines from the edit script, so they
   do not appear in formatted output. Summary stats still use raw line counts.
4. **Identical inputs:** unified output is empty; inline and side-by-side print
   the full edit script; summary/`--stat` print stats.
5. **Word diff** applies to paired delete/insert lines only; tokens come from
   `str.split()` and render with single-space joins.

## Trade-Off

Display choices favor stable CLI output over showing both originals on every
equal line. Word diff does not preserve original intra-line whitespace.

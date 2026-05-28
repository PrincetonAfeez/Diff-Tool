# ADR 0003: Formatters Separated From Engine

## Decision

The engine returns structured diff data. Formatters render that data.

## Rationale

Adding a new output format should not require changing the LCS algorithm.

## Dependency Direction

The CLI calls the engine and a formatter. Formatters depend on models, not on
engine internals.

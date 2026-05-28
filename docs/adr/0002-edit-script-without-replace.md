# ADR 0002: Edit Script Without Replace

## Decision

Represent changed lines as `DELETE` followed by `INSERT`.

## Rationale

This keeps the model faithful to LCS. A replacement is a formatter-level idea,
not a core algorithm operation.

## Trade-Off

Formatters may need to visually group adjacent delete/insert pairs.

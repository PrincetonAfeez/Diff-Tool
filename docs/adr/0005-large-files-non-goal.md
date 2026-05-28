# ADR 0005: Large Files Are A Non-Goal

## Decision

Do not optimize for very large files in Version 1.

## Rationale

The selected LCS algorithm uses `O(n x m)` memory. The project favors readable
algorithmic implementation over memory optimization.

## Safeguard

The engine accepts a maximum table-cell limit and raises a clean error before
allocating an oversized table.

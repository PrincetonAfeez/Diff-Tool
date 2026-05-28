# ADR 0001: Plain LCS DP Table

## Decision

Use the classic `O(n x m)` dynamic-programming table for LCS.

## Rationale

The goal is algorithmic clarity. The full table is easy to inspect, test, and
backtrace.

## Backtrace Tie-Breaking

When both non-equal moves yield the same DP score, backtrace chooses INSERT
first. After the step list is reversed, the forward edit script prefers DELETE
before INSERT for single-line replacements.

Duplicate-line alignment follows the same deterministic rule but may delete an
earlier duplicate while matching a later one. This is one valid LCS optimum,
not a unique alignment.

## Trade-Off

Memory grows with the product of the two input lengths. Very large files are a
documented non-goal for this version.

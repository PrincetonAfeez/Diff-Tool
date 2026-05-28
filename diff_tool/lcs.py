"""Classic O(n x m) Longest Common Subsequence implementation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from diff_tool.errors import DiffAlgorithmError
from diff_tool.models import Operation

T = TypeVar("T")
BacktraceStep = tuple[Operation, int | None, int | None]


def build_lcs_table(
    a: Sequence[T],
    b: Sequence[T],
    *,
    max_cells: int | None = None,
) -> list[list[int]]:
    """Build the LCS DP table for two comparable sequences."""

    cell_count = (len(a) + 1) * (len(b) + 1)
    if max_cells is not None and cell_count > max_cells:
        raise DiffAlgorithmError(
            "input is too large for the plain O(n x m) LCS table "
            f"({cell_count:,} cells exceeds limit of {max_cells:,})"
        )

    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]

    for i, old_item in enumerate(a, start=1):
        previous_row = table[i - 1]
        row = table[i]
        for j, new_item in enumerate(b, start=1):
            if old_item == new_item:
                row[j] = previous_row[j - 1] + 1
            else:
                row[j] = max(previous_row[j], row[j - 1])

    return table


def backtrace_lcs(
    a: Sequence[T],
    b: Sequence[T],
    table: list[list[int]],
) -> list[BacktraceStep]:
    """Recover an edit script from a completed LCS table.

    On equal DP scores the backtrace chooses INSERT first. After reversal,
    the edit script prefers DELETE before INSERT for changed lines.
    """

    i = len(a)
    j = len(b)
    steps: list[BacktraceStep] = []

    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            steps.append((Operation.EQUAL, i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or table[i - 1][j] > table[i][j - 1]):
            steps.append((Operation.DELETE, i - 1, None))
            i -= 1
        else:
            steps.append((Operation.INSERT, None, j - 1))
            j -= 1

    steps.reverse()
    return steps


def lcs_steps(
    a: Sequence[T],
    b: Sequence[T],
    *,
    max_cells: int | None = None,
) -> list[BacktraceStep]:
    """Build and backtrace an LCS table in one call."""

    table = build_lcs_table(a, b, max_cells=max_cells)
    return backtrace_lcs(a, b, table)

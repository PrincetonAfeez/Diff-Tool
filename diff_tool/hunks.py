"""Hunk grouping for display formats."""

from __future__ import annotations

from diff_tool.errors import InvalidOptionError
from diff_tool.models import Edit, Hunk, Operation


def build_hunks(edits: list[Edit], *, context_lines: int = 3) -> list[Hunk]:
    if context_lines < 0:
        raise InvalidOptionError("context_lines must be zero or greater")

    change_indexes = [
        index for index, edit in enumerate(edits) if edit.op is not Operation.EQUAL
    ]
    if not change_indexes:
        return []

    ranges: list[tuple[int, int]] = []
    for change_index in change_indexes:
        start = max(0, change_index - context_lines)
        end = min(len(edits), change_index + context_lines + 1)
        if ranges and start <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))

    return [_make_hunk(edits[start:end]) for start, end in ranges]


def _make_hunk(edits: list[Edit]) -> Hunk:
    old_count = sum(1 for edit in edits if edit.old_line_no is not None)
    new_count = sum(1 for edit in edits if edit.new_line_no is not None)

    old_start = _first_line_no(edits, side="old", count=old_count)
    new_start = _first_line_no(edits, side="new", count=new_count)

    return Hunk(
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
        edits=tuple(edits),
    )


def _first_line_no(edits: list[Edit], *, side: str, count: int) -> int:
    """Return the first line number on a side, or 0 when that side is empty.

    Unified diff headers use ``-0,0`` / ``+0,0`` for empty sides (Git style).
    """

    del count  # kept for call-site clarity; empty sides always return 0
    for edit in edits:
        line_no = edit.old_line_no if side == "old" else edit.new_line_no
        if line_no is not None:
            return line_no
    return 0

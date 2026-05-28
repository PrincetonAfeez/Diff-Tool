"""Hunk grouping tests."""

import pytest

from diff_tool.engine import diff_lines
from diff_tool.errors import InvalidOptionError
from diff_tool.hunks import build_hunks, _first_line_no, _make_hunk
from diff_tool.models import DiffOptions, Edit, Operation


def test_build_hunks_no_changes_returns_empty():
    result = diff_lines(["a"], ["a"])

    assert build_hunks(list(result.edits)) == []


def test_build_hunks_single_change_one_hunk():
    result = diff_lines(["a", "b", "c"], ["a", "x", "c"])

    hunks = build_hunks(list(result.edits), context_lines=3)

    assert len(hunks) == 1
    assert hunks[0].old_start == 1
    assert hunks[0].new_start == 1


def test_build_hunks_nearby_changes_merge():
    result = diff_lines(
        ["a", "b", "c", "d"],
        ["a", "x", "y", "d"],
        DiffOptions(context_lines=3),
    )

    assert len(build_hunks(list(result.edits))) == 1


def test_build_hunks_negative_context_raises():
    with pytest.raises(InvalidOptionError):
        build_hunks([], context_lines=-1)


def test_make_hunk_counts_lines_per_side():
    edits = [
        Edit(op=Operation.DELETE, old_line_no=2, old_text="b"),
        Edit(op=Operation.INSERT, new_line_no=2, new_text="x"),
    ]
    hunk = _make_hunk(edits)

    assert hunk.old_count == 1
    assert hunk.new_count == 1
    assert hunk.old_start == 2
    assert hunk.new_start == 2


def test_first_line_no_returns_zero_for_empty_side():
    edits = [Edit(op=Operation.INSERT, new_line_no=1, new_text="a")]

    assert _first_line_no(edits, side="old", count=0) == 0
    assert _first_line_no(edits, side="new", count=1) == 1


def test_build_hunks_context_zero_only_changed_lines():
    result = diff_lines(
        ["a", "b", "c", "d", "e"],
        ["a", "x", "c", "d", "y"],
        DiffOptions(context_lines=0),
    )

    for hunk in result.hunks:
        assert all(
            edit.op is not Operation.EQUAL or edit.old_text in {"a", "c", "d", "e"}
            for edit in hunk.edits
        )

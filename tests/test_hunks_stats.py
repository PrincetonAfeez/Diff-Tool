"""Tests for the hunks and stats."""

from diff_tool.engine import diff_lines
from diff_tool.hunks import build_hunks
from diff_tool.models import DiffOptions, Operation


def test_hunks_split_distant_changes():
    result = diff_lines(
        ["a", "b", "c", "d", "e", "f"],
        ["a", "x", "c", "d", "y", "f"],
        DiffOptions(context_lines=0),
    )

    assert len(result.hunks) == 2


def test_stats_count_changed_run_as_max_deletes_or_inserts():
    result = diff_lines(["a", "b", "c"], ["a", "x", "y", "c"])

    assert result.stats.insert_count == 2
    assert result.stats.delete_count == 1
    assert result.stats.changed_count == 2
    assert result.stats.similarity == 50.0


def test_hunks_include_context_lines_around_change():
    result = diff_lines(
        ["a", "b", "c", "d", "e"],
        ["a", "x", "c", "d", "e"],
        DiffOptions(context_lines=1),
    )

    hunk = result.hunks[0]
    ops = [edit.op for edit in hunk.edits]
    assert Operation.EQUAL in ops
    assert Operation.DELETE in ops
    assert Operation.INSERT in ops


def test_build_hunks_via_engine_matches_direct_call():
    result = diff_lines(["a", "b"], ["a", "c"], DiffOptions(context_lines=0))

    direct = build_hunks(list(result.edits), context_lines=0)

    assert len(direct) == len(result.hunks)
    assert direct[0].old_start == result.hunks[0].old_start

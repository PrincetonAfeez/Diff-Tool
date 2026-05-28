"""Statistics calculation tests."""

from diff_tool.engine import diff_lines
from diff_tool.models import Edit, Operation
from diff_tool.stats import _count_changed_lines, calculate_stats


def test_calculate_stats_identical_all_equal():
    result = diff_lines(["a", "b"], ["a", "b"])

    stats = result.stats

    assert stats.equal_count == 2
    assert stats.insert_count == 0
    assert stats.delete_count == 0
    assert stats.changed_count == 0
    assert stats.similarity == 100.0


def test_calculate_stats_empty_files():
    stats = calculate_stats([], old_line_count=0, new_line_count=0)

    assert stats.similarity == 100.0
    assert stats.equal_count == 0


def test_count_changed_lines_multiple_runs():
    edits = [
        Edit(op=Operation.EQUAL, old_text="a"),
        Edit(op=Operation.DELETE, old_text="b"),
        Edit(op=Operation.DELETE, old_text="c"),
        Edit(op=Operation.INSERT, new_text="x"),
        Edit(op=Operation.EQUAL, old_text="d"),
        Edit(op=Operation.DELETE, old_text="e"),
        Edit(op=Operation.INSERT, new_text="y"),
        Edit(op=Operation.INSERT, new_text="z"),
    ]

    assert _count_changed_lines(edits) == 4  # max(2,1) + max(1,2)


def test_calculate_stats_only_inserts():
    stats = calculate_stats(
        [Edit(op=Operation.INSERT, new_text="a")],
        old_line_count=0,
        new_line_count=1,
    )

    assert stats.similarity == 0.0
    assert stats.insert_count == 1

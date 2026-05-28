"""Direct tests for backtrace_lcs (separate from lcs_steps integration)."""

import pytest

from diff_tool.lcs import backtrace_lcs, build_lcs_table
from diff_tool.models import Operation


@pytest.mark.parametrize(
    "a,b,expected_ops",
    [
        ([], [], []),
        (["a"], ["a"], [Operation.EQUAL]),
        ([], ["x"], [Operation.INSERT]),
        (["x"], [], [Operation.DELETE]),
        (
            ["a", "b", "c"],
            ["a", "c"],
            [Operation.EQUAL, Operation.DELETE, Operation.EQUAL],
        ),
        (
            ["a", "b"],
            ["a", "x", "b"],
            [Operation.EQUAL, Operation.INSERT, Operation.EQUAL],
        ),
    ],
)
def test_backtrace_lcs_operation_sequence(a, b, expected_ops):
    table = build_lcs_table(a, b)
    steps = backtrace_lcs(a, b, table)

    assert [op for op, _, _ in steps] == expected_ops


def test_backtrace_lcs_delete_at_start():
    table = build_lcs_table(["old"], ["new"])
    steps = backtrace_lcs(["old"], ["new"], table)

    assert [op for op, _, _ in steps] == [Operation.DELETE, Operation.INSERT]


def test_backtrace_lcs_insert_at_end():
    table = build_lcs_table(["a"], ["a", "b"])
    steps = backtrace_lcs(["a"], ["a", "b"], table)

    assert [op for op, _, _ in steps] == [Operation.EQUAL, Operation.INSERT]


def test_backtrace_lcs_repeated_equal_lines():
    table = build_lcs_table(["A", "A", "B"], ["A", "B", "A"])
    steps = backtrace_lcs(["A", "A", "B"], ["A", "B", "A"], table)

    assert [op for op, _, _ in steps] == [
        Operation.DELETE,
        Operation.EQUAL,
        Operation.EQUAL,
        Operation.INSERT,
    ]

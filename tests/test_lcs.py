import pytest

from diff_tool.errors import DiffAlgorithmError
from diff_tool.lcs import build_lcs_table, lcs_steps
from diff_tool.models import Operation


def test_build_lcs_table_records_lengths():
    table = build_lcs_table(["a", "b", "c"], ["a", "c"])

    assert table[-1][-1] == 2


def test_lcs_steps_for_changed_line_delete_then_insert():
    steps = lcs_steps(["a", "b", "c"], ["a", "x", "c"])

    assert [step[0] for step in steps] == [
        Operation.EQUAL,
        Operation.DELETE,
        Operation.INSERT,
        Operation.EQUAL,
    ]


def test_lcs_steps_empty_vs_non_empty():
    steps = lcs_steps([], ["a", "b"])

    assert steps == [
        (Operation.INSERT, None, 0),
        (Operation.INSERT, None, 1),
    ]


def test_lcs_steps_empty_vs_empty():
    assert lcs_steps([], []) == []


def test_lcs_steps_prefers_delete_before_insert_in_forward_script():
    steps = lcs_steps(["a"], ["b"])

    assert [step[0] for step in steps] == [
        Operation.DELETE,
        Operation.INSERT,
    ]


def test_lcs_steps_duplicate_line_alignment_is_deterministic():
    steps = lcs_steps(["A", "A", "B"], ["A", "B", "A"])

    assert [step[0] for step in steps] == [
        Operation.DELETE,
        Operation.EQUAL,
        Operation.EQUAL,
        Operation.INSERT,
    ]


def test_build_lcs_table_identical_sequences():
    table = build_lcs_table(["a", "b"], ["a", "b"])

    assert table[2][2] == 2


def test_build_lcs_table_completely_different():
    table = build_lcs_table(["a", "b"], ["c", "d"])

    assert table[-1][-1] == 0


def test_build_lcs_table_max_cells_raises():
    with pytest.raises(DiffAlgorithmError, match="exceeds limit"):
        build_lcs_table(["a", "b"], ["c", "d"], max_cells=4)


def test_lcs_steps_identical_sequences_all_equal():
    steps = lcs_steps(["x", "y"], ["x", "y"])

    assert all(step[0] is Operation.EQUAL for step in steps)
    assert len(steps) == 2

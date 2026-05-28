"""Dataclass and property behavior."""

from diff_tool.engine import diff_lines
from diff_tool.models import DiffOptions, FileInput, Operation


def test_file_input_single_line_ending_not_mixed():
    file_input = FileInput(label="x", lines=["a"], line_endings=("\n",))

    assert not file_input.mixed_line_endings


def test_diff_result_has_changes_false_when_identical():
    result = diff_lines(["a"], ["a"])

    assert not result.has_changes


def test_diff_result_has_changes_true_on_insert_only():
    result = diff_lines([], ["a"])

    assert result.has_changes
    assert result.stats.insert_count == 1
    assert result.stats.delete_count == 0


def test_diff_result_has_changes_true_on_delete_only():
    result = diff_lines(["a"], [])

    assert result.has_changes
    assert result.stats.delete_count == 1


def test_diff_options_defaults():
    options = DiffOptions()

    assert options.context_lines == 3
    assert options.max_table_cells == 2_000_000
    assert not options.word_diff


def test_operation_enum_values():
    assert Operation.EQUAL.value == "equal"
    assert Operation.INSERT.value == "insert"
    assert Operation.DELETE.value == "delete"

"""Tests for the diff engine."""

import pytest

from diff_tool.engine import _add_word_diffs, diff_lines
from diff_tool.errors import DiffAlgorithmError, InvalidOptionError
from diff_tool.models import DiffOptions, Edit, Operation

from tests.conftest import apply_edit_script


def test_diff_lines_reconstructs_new_input():
    old = ["alpha", "bravo", "charlie"]
    new = ["alpha", "delta", "charlie", "echo"]
    result = diff_lines(old, new)

    assert apply_edit_script(result.edits) == new
    assert [edit.op for edit in result.edits] == [
        Operation.EQUAL,
        Operation.DELETE,
        Operation.INSERT,
        Operation.EQUAL,
        Operation.INSERT,
    ]


def test_ignore_case_preserves_original_display_text():
    result = diff_lines(["Hello"], ["hello"], DiffOptions(ignore_case=True))

    assert not result.has_changes
    assert result.edits[0].old_text == "Hello"
    assert result.edits[0].new_text == "hello"


def test_ignore_trailing_space_treats_lines_as_equal():
    result = diff_lines(["alpha  "], ["alpha"], DiffOptions(ignore_trailing_space=True))

    assert not result.has_changes
    assert result.edits[0].old_text == "alpha  "
    assert result.edits[0].new_text == "alpha"


def test_ignore_all_space_compares_without_destroying_output():
    result = diff_lines(
        ["hello world"], ["helloworld"], DiffOptions(ignore_all_space=True)
    )

    assert not result.has_changes
    assert result.edits[0].old_text == "hello world"
    assert result.edits[0].new_text == "helloworld"


def test_ignore_blank_lines_filters_comparison_with_original_line_numbers():
    result = diff_lines(
        ["alpha", "", "bravo"],
        ["alpha", "bravo"],
        DiffOptions(ignore_blank_lines=True),
    )

    assert not result.has_changes
    assert [(edit.old_line_no, edit.new_line_no) for edit in result.edits] == [
        (1, 1),
        (3, 2),
    ]
    assert result.stats.similarity == 100.0
    assert result.stats.old_line_count == 3
    assert result.stats.new_line_count == 2


def test_word_diff_attaches_token_edits_to_simple_changed_pair():
    result = diff_lines(
        ["The quick brown fox"],
        ["The quick red fox"],
        DiffOptions(word_diff=True),
    )

    delete_edit, insert_edit = result.edits
    assert delete_edit.op is Operation.DELETE
    assert insert_edit.op is Operation.INSERT
    assert len(delete_edit.word_edits) == len(insert_edit.word_edits)


def test_word_diff_pairs_multi_line_change_blocks():
    result = diff_lines(
        ["line1 old", "line2 old"],
        ["line1 new", "line2 new"],
        DiffOptions(word_diff=True),
    )

    delete_one, delete_two, insert_one, insert_two = result.edits
    assert delete_one.word_edits
    assert insert_one.word_edits
    assert delete_one.word_edits == insert_one.word_edits
    assert delete_two.word_edits
    assert insert_two.word_edits
    assert delete_two.word_edits == insert_two.word_edits
    assert any(
        edit.op is Operation.DELETE and edit.old_token == "old"
        for edit in delete_two.word_edits
    )


def test_max_table_cells_guard_raises_clean_algorithm_error():
    with pytest.raises(DiffAlgorithmError):
        diff_lines(["a", "b"], ["c", "d"], DiffOptions(max_table_cells=4))


def test_negative_context_lines_raises_invalid_option_error():
    with pytest.raises(InvalidOptionError):
        diff_lines(["a"], ["b"], DiffOptions(context_lines=-1))


def test_max_table_cells_below_one_raises_invalid_option_error():
    with pytest.raises(InvalidOptionError):
        diff_lines([], [], DiffOptions(max_table_cells=0))


def test_empty_diff_with_min_table_cells_succeeds():
    result = diff_lines([], [], DiffOptions(max_table_cells=1))

    assert not result.has_changes
    assert result.edits == ()


def test_diff_result_exposes_immutable_sequences():
    result = diff_lines(["a"], ["b"])

    assert isinstance(result.edits, tuple)
    assert isinstance(result.hunks, tuple)


@pytest.mark.parametrize(
    "old_lines,new_lines",
    [
        ([], []),
        (["only"], ["only"]),
        (["a", "b", "c"], ["a", "b", "c"]),
    ],
)
def test_diff_lines_reconstructs_parametrized(old_lines, new_lines):
    result = diff_lines(old_lines, new_lines)

    assert apply_edit_script(result.edits) == new_lines
    assert not result.has_changes


def test_diff_lines_identical_produces_no_hunks_in_unified():
    result = diff_lines(["x"], ["x"])

    assert not result.has_changes
    assert result.hunks == ()


def test_diff_lines_combined_ignore_case_and_trailing_space():
    result = diff_lines(
        ["Hello  "],
        ["hello"],
        DiffOptions(ignore_case=True, ignore_trailing_space=True),
    )

    assert not result.has_changes


def test_add_word_diffs_skips_edits_without_text():
    edits = [
        Edit(op=Operation.DELETE, old_text=None),
        Edit(op=Operation.INSERT, new_text=None),
        Edit(op=Operation.DELETE, old_text="a"),
        Edit(op=Operation.INSERT, new_text="b"),
    ]

    updated = _add_word_diffs(edits, max_table_cells=1_000_000)

    assert updated[0].word_edits == ()
    assert updated[1].word_edits == ()
    assert updated[2].word_edits
    assert updated[3].word_edits == updated[2].word_edits


def test_word_diff_unpaired_extra_deletes_have_no_token_edits():
    result = diff_lines(
        ["one", "two", "three"],
        ["one", "four"],
        DiffOptions(word_diff=True),
    )

    deletes = [e for e in result.edits if e.op is Operation.DELETE]
    assert len(deletes) == 2
    assert deletes[-1].word_edits == ()

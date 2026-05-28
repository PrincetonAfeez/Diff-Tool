"""Token-level diff and render helpers."""

import pytest

from diff_tool.errors import DiffAlgorithmError
from diff_tool.lcs import lcs_steps
from diff_tool.models import Operation, TokenEdit
from diff_tool.word_diff import (
    diff_tokens,
    render_deleted_tokens,
    render_inserted_tokens,
)


def test_diff_tokens_detects_word_change():
    edits = diff_tokens("The quick brown fox", "The quick red fox")

    assert any(e.op is Operation.DELETE and e.old_token == "brown" for e in edits)
    assert any(e.op is Operation.INSERT and e.new_token == "red" for e in edits)
    assert any(e.op is Operation.EQUAL and e.old_token == "quick" for e in edits)


def test_diff_tokens_empty_strings():
    assert diff_tokens("", "") == ()


def test_diff_tokens_single_word_insert():
    edits = diff_tokens("hello", "hello world")

    assert [e.op for e in edits] == [
        Operation.EQUAL,
        Operation.INSERT,
    ]


def test_diff_tokens_max_table_cells_guard():
    with pytest.raises(DiffAlgorithmError):
        diff_tokens("a b c", "d e f", max_table_cells=4)


def test_render_deleted_tokens_uses_fallback_when_empty():
    assert render_deleted_tokens((), "full line") == "full line"


def test_render_deleted_tokens_marks_deletions():
    edits = (
        TokenEdit(Operation.EQUAL, old_token="The", new_token="The"),
        TokenEdit(Operation.DELETE, old_token="brown"),
    )

    assert render_deleted_tokens(edits, "fallback") == "The [-brown-]"


def test_render_inserted_tokens_uses_fallback_when_empty():
    assert render_inserted_tokens((), "full line") == "full line"


def test_render_inserted_tokens_marks_insertions():
    edits = (
        TokenEdit(Operation.EQUAL, old_token="The", new_token="The"),
        TokenEdit(Operation.INSERT, new_token="red"),
    )

    assert render_inserted_tokens(edits, "fallback") == "The {+red+}"


def test_token_lcs_steps_reconstruct_new_tokens():
    old_tokens = "one two three".split()
    new_tokens = "one four three".split()
    steps = lcs_steps(old_tokens, new_tokens)

    output: list[str] = []
    for op, old_index, new_index in steps:
        if op is Operation.EQUAL:
            output.append(new_tokens[new_index])  # type: ignore[index]
        elif op is Operation.INSERT:
            output.append(new_tokens[new_index])  # type: ignore[index]

    assert output == new_tokens

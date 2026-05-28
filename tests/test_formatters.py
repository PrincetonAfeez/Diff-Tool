""" Tests for the formatters """

import pytest

from diff_tool.color import RED
from diff_tool.engine import diff_lines
from diff_tool.formatters import (
    format_inline,
    format_side_by_side,
    format_summary,
    format_unified,
)
from diff_tool.formatters.side_by_side import _clip
from diff_tool.errors import InvalidOptionError
from diff_tool.models import DiffOptions


def test_unified_formatter_outputs_hunk():
    result = diff_lines(["a", "b", "c"], ["a", "x", "c"])

    output = format_unified(result, old_label="old.txt", new_label="new.txt")

    assert "--- old.txt" in output
    assert "+++ new.txt" in output
    assert "@@ -1,3 +1,3 @@" in output
    assert "-b" in output
    assert "+x" in output


def test_unified_formatter_pure_insert_uses_git_style_header():
    result = diff_lines([], ["a", "b"])

    output = format_unified(result)

    assert "@@ -0,0 +1,2 @@" in output
    assert "+a" in output
    assert "+b" in output


def test_word_diff_markers_render_in_unified_output():
    result = diff_lines(
        ["The quick brown fox"],
        ["The quick red fox"],
        DiffOptions(word_diff=True),
    )

    output = format_unified(result)

    assert "[-brown-]" in output
    assert "{+red+}" in output


def test_summary_formatter_outputs_counts():
    result = diff_lines(["a"], ["a", "b"])

    output = format_summary(result)

    assert "Status: different" in output
    assert "Inserted lines: +1" in output


def test_summary_formatter_identical_files():
    result = diff_lines(["a"], ["a"])

    output = format_summary(result)

    assert "Status: identical" in output


def test_inline_formatter_outputs_single_stream():
    result = diff_lines(["a"], ["b"])

    assert format_inline(result).splitlines() == ["- a", "+ b"]


def test_side_by_side_formatter_outputs_columns():
    result = diff_lines(["a"], ["b"])

    output = format_side_by_side(result, width=40)

    assert "<" in output
    assert ">" in output


def test_side_by_side_respects_exact_width():
    result = diff_lines(["a"], ["b"])

    for line in format_side_by_side(result, width=40).splitlines():
        assert len(line) == 40


def test_side_by_side_ignore_case_shows_matching_columns():
    result = diff_lines(["Hello"], ["hello"], DiffOptions(ignore_case=True))

    output = format_side_by_side(result, width=40)

    assert "Hello" in output
    assert "hello" not in output.split("Hello", 1)[-1].strip()


def test_word_diff_markers_render_in_inline_output():
    result = diff_lines(
        ["The quick brown fox"],
        ["The quick red fox"],
        DiffOptions(word_diff=True),
    )

    output = format_inline(result)

    assert "[-brown-]" in output
    assert "{+red+}" in output


def test_inline_formatter_prints_identical_files():
    result = diff_lines(["a", "b"], ["a", "b"])

    assert format_inline(result).splitlines() == ["  a", "  b"]


def test_side_by_side_width_below_minimum_raises():
    result = diff_lines(["a"], ["b"])

    with pytest.raises(InvalidOptionError):
        format_side_by_side(result, width=20)


def test_unified_formatter_no_output_when_identical():
    result = diff_lines(["a"], ["a"])

    assert format_unified(result) == ""


def test_unified_formatter_color_enabled():
    result = diff_lines(["a"], ["b"])

    output = format_unified(result, color=True)

    assert RED in output
    assert "\033[" in output


def test_inline_formatter_color_enabled():
    result = diff_lines(["a"], ["b"])

    output = format_inline(result, color=True)

    assert "\033[31m" in output
    assert "\033[32m" in output


def test_side_by_side_clips_long_lines():
    assert _clip("abcdefghij", 5) == "ab..."
    assert _clip("ab", 5) == "ab"
    assert _clip("abcdef", 3) == "abc"


def test_side_by_side_color_enabled():
    result = diff_lines(["a"], ["b"])

    output = format_side_by_side(result, width=40, color=True)

    assert "\033[31m" in output or "\033[32m" in output


def test_side_by_side_word_diff_on_delete_insert():
    result = diff_lines(
        ["The quick brown fox"],
        ["The quick red fox"],
        DiffOptions(word_diff=True),
    )

    output = format_side_by_side(result, width=80)

    assert "[-brown-]" in output
    assert "{+red+}" in output


def test_summary_formatter_includes_similarity():
    result = diff_lines(["a", "b", "c"], ["a", "x", "c"])

    output = format_summary(result)

    assert "Similarity:" in output
    assert "%" in output

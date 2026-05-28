"""Tests for the examples directory."""

from pathlib import Path

from diff_tool.engine import diff_lines
from diff_tool.formatters import format_unified
from diff_tool.models import DiffOptions

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_example_lines(name: str) -> list[str]:
    return (EXAMPLES / name).read_text(encoding="utf-8").splitlines()


def test_examples_directory_diff_detects_changes():
    result = diff_lines(_load_example_lines("old.txt"), _load_example_lines("new.txt"))

    assert result.has_changes
    assert result.stats.insert_count == 2
    assert result.stats.delete_count == 1


def test_examples_unified_output_matches_golden_file():
    result = diff_lines(_load_example_lines("old.txt"), _load_example_lines("new.txt"))
    expected = (FIXTURES / "examples_unified.golden").read_text(encoding="utf-8")

    output = format_unified(result, old_label="old.txt", new_label="new.txt")

    assert output == expected.rstrip("\n")


def test_examples_word_diff_highlights_changed_words():
    result = diff_lines(
        _load_example_lines("old.txt"),
        _load_example_lines("new.txt"),
        DiffOptions(word_diff=True),
    )

    changed_delete = next(edit for edit in result.edits if edit.old_text == "bravo")
    assert changed_delete.word_edits

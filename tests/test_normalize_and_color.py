"""Tests for the normalization and colorization."""

import io

from diff_tool.color import CYAN, ColorMode, RED, colorize, should_color
from diff_tool.models import DiffOptions
from diff_tool.normalize import normalize_line, prepare_lines


def test_normalize_line_ignore_trailing_space():
    options = DiffOptions(ignore_trailing_space=True)

    assert normalize_line("alpha  ", options) == "alpha"


def test_normalize_line_ignore_all_space():
    options = DiffOptions(ignore_all_space=True)

    assert normalize_line("hello world", options) == "helloworld"


def test_prepare_lines_skips_blank_lines_when_configured():
    options = DiffOptions(ignore_blank_lines=True)

    prepared = prepare_lines(["alpha", "", "bravo"], options)

    assert [line.text for line in prepared] == ["alpha", "bravo"]
    assert [line.line_no for line in prepared] == [1, 3]


def test_should_color_respects_no_color_env(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")

    assert not should_color(ColorMode.ALWAYS.value)


def test_should_color_always_and_never(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    stream = io.StringIO()

    assert should_color(ColorMode.ALWAYS.value, stream=stream)
    assert not should_color(ColorMode.NEVER.value, stream=stream)


def test_colorize_disabled_returns_plain_text():
    assert colorize("hello", "\033[31m", enabled=False) == "hello"


def test_normalize_line_default_returns_unchanged():
    assert normalize_line("  hello  ", DiffOptions()) == "  hello  "


def test_normalize_line_ignore_case():
    options = DiffOptions(ignore_case=True)

    assert normalize_line("Hello", options) == "hello"


def test_normalize_line_combined_options():
    options = DiffOptions(
        ignore_trailing_space=True,
        ignore_all_space=True,
        ignore_case=True,
    )

    assert normalize_line("  Hello   World  ", options) == "helloworld"


def test_prepare_lines_keeps_blank_lines_by_default():
    prepared = prepare_lines(["a", "", "b"], DiffOptions())

    assert [line.text for line in prepared] == ["a", "", "b"]


def test_should_color_auto_uses_tty_when_available(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)

    class TtyStream:
        def isatty(self):
            return True

    assert should_color(ColorMode.AUTO.value, stream=TtyStream())


def test_should_color_auto_false_without_tty(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)

    assert not should_color(ColorMode.AUTO.value, stream=io.StringIO())


def test_colorize_enabled_wraps_with_escape_codes():
    result = colorize("line", RED, enabled=True)

    assert result.startswith(RED)
    assert "line" in result
    assert result.endswith("\033[0m")


def test_color_constants_are_ansi_sequences():
    assert CYAN.startswith("\033[")

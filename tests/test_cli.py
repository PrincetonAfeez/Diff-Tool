"""Tests for the command-line interface."""

import io as stdlib_io

import pytest

from diff_tool.cli import build_parser, main


def test_cli_identical_files_exit_zero(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("a\n", encoding="utf-8")

    exit_code = main([str(old), str(new)])

    assert exit_code == 0
    assert capsys.readouterr().out == ""


def test_cli_different_files_exit_one_and_print_diff(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    exit_code = main([str(old), str(new)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "-a" in output
    assert "+b" in output


def test_cli_missing_file_exits_two(tmp_path, capsys):
    new = tmp_path / "new.txt"
    new.write_text("b\n", encoding="utf-8")

    exit_code = main([str(tmp_path / "missing.txt"), str(new)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "error:" in captured.err


def test_cli_stdin_works(tmp_path, monkeypatch, capsys):
    new = tmp_path / "new.txt"
    new.write_text("a\nb\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", stdlib_io.StringIO("a\n"))

    exit_code = main(["-", str(new), "--format", "summary"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Inserted lines: +1" in captured.out


def test_cli_both_stdin_fails(capsys):
    exit_code = main(["-", "-"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "both inputs cannot be stdin" in captured.err


def test_cli_no_color_disables_ansi(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    main([str(old), str(new), "--color", "always", "--no-color"])

    assert "\033[" not in capsys.readouterr().out


def test_cli_stat_flag_shows_summary(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("a\nb\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--stat"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Status: different" in captured.out
    assert "Similarity:" in captured.out


def test_cli_ignore_trailing_space(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("alpha  \n", encoding="utf-8")
    new.write_text("alpha\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--ignore-trailing-space"])

    assert exit_code == 0
    assert capsys.readouterr().out == ""


def test_cli_negative_context_exits_two(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--context", "-1"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "context must be zero or greater" in captured.err


def test_cli_width_too_small_exits_two(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--width", "20"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "width must be at least 40" in captured.err


def test_cli_warns_on_mixed_line_endings(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_bytes(b"a\r\nb\n")
    new.write_text("a\n", encoding="utf-8")

    main([str(old), str(new)])
    captured = capsys.readouterr()

    assert "warning: mixed line endings detected" in captured.err


def test_cli_max_table_cells_guard(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\nb\n", encoding="utf-8")
    new.write_text("c\nd\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--max-table-cells", "4"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "too large for the plain O(n x m) LCS table" in captured.err


def test_cli_max_table_cells_below_one_exits_two(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("a\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--max-table-cells", "0"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "max-table-cells must be at least 1" in captured.err


def test_cli_word_diff_flag(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("The quick brown fox\n", encoding="utf-8")
    new.write_text("The quick red fox\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--word-diff"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "[-brown-]" in output
    assert "{+red+}" in output


def test_cli_ignore_blank_lines_omits_blanks_from_output(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("alpha\n\nbravo\n", encoding="utf-8")
    new.write_text("alpha\nbravo\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--ignore-blank-lines"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""


def test_cli_identical_files_with_stat_prints_summary(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("a\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--stat"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Status: identical" in captured.out


def test_cli_inline_format_on_different_files(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--format", "inline"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "- a" in output
    assert "+ b" in output


def test_cli_side_by_side_format_on_different_files(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--format", "side-by-side", "--width", "40"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "<" in output
    assert ">" in output


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "diff-tool" in capsys.readouterr().out


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["old.txt", "new.txt"])

    assert args.format == "unified"
    assert args.context == 3
    assert args.width == 100
    assert args.color == "auto"
    assert args.max_table_cells == 2_000_000


def test_build_parser_format_choices():
    parser = build_parser()

    args = parser.parse_args(["a", "b", "--format", "summary"])
    assert args.format == "summary"


def test_cli_format_summary(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("a\nb\n", encoding="utf-8")

    exit_code = main([str(old), str(new), "--format", "summary"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Status: different" in captured.out


def test_cli_ignore_case(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("Hello\n", encoding="utf-8")
    new.write_text("hello\n", encoding="utf-8")

    assert main([str(old), str(new), "--ignore-case"]) == 0


def test_cli_color_always_enables_ansi(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    main([str(old), str(new), "--color", "always"])
    output = capsys.readouterr().out

    assert "\x1b[" in output or "\033[" in output


def test_cli_broken_pipe_returns_two(tmp_path, monkeypatch):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("a\n", encoding="utf-8")
    new.write_text("b\n", encoding="utf-8")

    def raise_broken_pipe(*args, **kwargs):
        raise BrokenPipeError

    monkeypatch.setattr("builtins.print", raise_broken_pipe)

    assert main([str(old), str(new)]) == 2


def test_cli_ignore_all_space(tmp_path, capsys):
    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text("hello world\n", encoding="utf-8")
    new.write_text("helloworld\n", encoding="utf-8")

    assert main([str(old), str(new), "--ignore-all-space"]) == 0

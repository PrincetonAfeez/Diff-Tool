"""argparse command-line interface for the diff tool."""

from __future__ import annotations

import argparse
import sys

from diff_tool import __version__
from diff_tool.color import should_color
from diff_tool.engine import diff_lines
from diff_tool.errors import CLIError, DiffToolError
from diff_tool.formatters import (
    format_inline,
    format_side_by_side,
    format_summary,
    format_unified,
)
from diff_tool.io import read_input
from diff_tool.models import DiffOptions, DiffResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diff-tool",
        description="Compare two text inputs using a hand-built LCS diff engine.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument("old", help='old file path, or "-" for stdin')
    parser.add_argument("new", help='new file path, or "-" for stdin')
    parser.add_argument(
        "--format",
        choices=["unified", "side-by-side", "inline", "summary"],
        default="unified",
        help="output format",
    )
    parser.add_argument("--stat", action="store_true", help="show summary output")
    parser.add_argument("-U", "--context", type=int, default=3, help="context lines")
    parser.add_argument(
        "--ignore-trailing-space",
        action="store_true",
        help="ignore trailing whitespace during comparison",
    )
    parser.add_argument(
        "--ignore-all-space",
        action="store_true",
        help="ignore all whitespace during comparison",
    )
    parser.add_argument(
        "--ignore-blank-lines",
        action="store_true",
        help="ignore blank lines during comparison",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="compare case-insensitively",
    )
    parser.add_argument(
        "--word-diff",
        action="store_true",
        help="highlight changed words in paired delete/insert lines",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="color output policy",
    )
    parser.add_argument("--no-color", action="store_true", help="disable color")
    parser.add_argument("--width", type=int, default=100, help="side-by-side width")
    parser.add_argument(
        "--max-table-cells",
        type=int,
        default=2_000_000,
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.old == "-" and args.new == "-":
            raise CLIError("both inputs cannot be stdin")
        if args.context < 0:
            raise CLIError("context must be zero or greater")
        if args.width < 40:
            raise CLIError("width must be at least 40")
        if args.max_table_cells < 1:
            raise CLIError("max-table-cells must be at least 1")

        stdin_text = sys.stdin.read() if "-" in (args.old, args.new) else None
        old_input = read_input(
            args.old, stdin_text=stdin_text if args.old == "-" else None
        )
        new_input = read_input(
            args.new, stdin_text=stdin_text if args.new == "-" else None
        )

        _warn_line_endings(old_input.label, old_input.mixed_line_endings)
        _warn_line_endings(new_input.label, new_input.mixed_line_endings)

        options = DiffOptions(
            ignore_trailing_space=args.ignore_trailing_space,
            ignore_all_space=args.ignore_all_space,
            ignore_blank_lines=args.ignore_blank_lines,
            ignore_case=args.ignore_case,
            context_lines=args.context,
            word_diff=args.word_diff,
            max_table_cells=args.max_table_cells,
        )
        result = diff_lines(old_input.lines, new_input.lines, options)
        color = should_color(args.color, stream=sys.stdout, no_color=args.no_color)
        output = _format_result(
            result,
            output_format="summary" if args.stat else args.format,
            old_label=old_input.label,
            new_label=new_input.label,
            width=args.width,
            color=color,
        )
        if output:
            print(output)
        return 1 if result.has_changes else 0
    except DiffToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 2


def _format_result(
    result: DiffResult,
    *,
    output_format: str,
    old_label: str,
    new_label: str,
    width: int,
    color: bool,
) -> str:
    if output_format == "unified":
        return format_unified(
            result,
            old_label=old_label,
            new_label=new_label,
            color=color,
        )
    if output_format == "side-by-side":
        return format_side_by_side(result, width=width, color=color)
    if output_format == "inline":
        return format_inline(result, color=color)
    return format_summary(result)


def _warn_line_endings(label: str, mixed: bool) -> None:
    if mixed:
        print(f"warning: mixed line endings detected in {label}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

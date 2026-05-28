"""Side-by-side formatter."""

from __future__ import annotations

from diff_tool.color import GREEN, RED, colorize
from diff_tool.errors import InvalidOptionError
from diff_tool.models import DiffResult, Edit, Operation
from diff_tool.word_diff import render_deleted_tokens, render_inserted_tokens

MIN_WIDTH = 40


def format_side_by_side(
    result: DiffResult,
    *,
    width: int = 100,
    color: bool = False,
) -> str:
    if width < MIN_WIDTH:
        raise InvalidOptionError(f"width must be at least {MIN_WIDTH}")
    gutter = 3  # " < " / " > " / "   "
    usable = width - gutter
    left_width = usable // 2
    right_width = usable - left_width
    lines: list[str] = []

    for edit in result.edits:
        marker = _marker(edit)
        left = _left_text(edit)
        right = _right_text(edit)
        line = f"{_clip(left, left_width):<{left_width}} {marker} {_clip(right, right_width):<{right_width}}"
        if edit.op is Operation.DELETE:
            line = colorize(line, RED, enabled=color)
        elif edit.op is Operation.INSERT:
            line = colorize(line, GREEN, enabled=color)
        lines.append(line)

    return "\n".join(lines)


def _marker(edit: Edit) -> str:
    if edit.op is Operation.EQUAL:
        return " "
    if edit.op is Operation.DELETE:
        return "<"
    return ">"


def _left_text(edit: Edit) -> str:
    if edit.op is Operation.INSERT:
        return ""
    if edit.op is Operation.EQUAL:
        return edit.old_text or ""
    return render_deleted_tokens(edit.word_edits, edit.old_text or "")


def _right_text(edit: Edit) -> str:
    if edit.op is Operation.DELETE:
        return ""
    if edit.op is Operation.EQUAL:
        return edit.old_text or ""
    return render_inserted_tokens(edit.word_edits, edit.new_text or "")


def _clip(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."

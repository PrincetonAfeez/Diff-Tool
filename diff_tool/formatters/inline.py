"""Narrow terminal inline formatter."""

from __future__ import annotations

from diff_tool.color import GREEN, RED, colorize
from diff_tool.models import DiffResult, Edit, Operation
from diff_tool.word_diff import render_deleted_tokens, render_inserted_tokens


def format_inline(result: DiffResult, *, color: bool = False) -> str:
    lines = [_format_edit(edit, color=color) for edit in result.edits]
    return "\n".join(lines)


def _format_edit(edit: Edit, *, color: bool) -> str:
    if edit.op is Operation.EQUAL:
        return f"  {edit.old_text if edit.old_text is not None else ''}"
    if edit.op is Operation.DELETE:
        text = render_deleted_tokens(edit.word_edits, edit.old_text or "")
        return colorize(f"- {text}", RED, enabled=color)

    text = render_inserted_tokens(edit.word_edits, edit.new_text or "")
    return colorize(f"+ {text}", GREEN, enabled=color)

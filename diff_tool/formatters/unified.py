"""Unified diff formatter."""

from __future__ import annotations

from diff_tool.color import CYAN, GREEN, RED, colorize
from diff_tool.models import DiffResult, Edit, Operation
from diff_tool.word_diff import render_deleted_tokens, render_inserted_tokens


def format_unified(
    result: DiffResult,
    *,
    old_label: str = "old",
    new_label: str = "new",
    color: bool = False,
) -> str:
    if not result.has_changes:
        return ""

    lines = [
        colorize(f"--- {old_label}", RED, enabled=color),
        colorize(f"+++ {new_label}", GREEN, enabled=color),
    ]

    for hunk in result.hunks:
        header = f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@"
        lines.append(colorize(header, CYAN, enabled=color))
        for edit in hunk.edits:
            lines.append(_format_edit(edit, color=color))

    return "\n".join(lines)


def _format_edit(edit: Edit, *, color: bool) -> str:
    if edit.op is Operation.EQUAL:
        return f" {edit.old_text if edit.old_text is not None else ''}"
    if edit.op is Operation.DELETE:
        text = render_deleted_tokens(edit.word_edits, edit.old_text or "")
        return colorize(f"-{text}", RED, enabled=color)

    text = render_inserted_tokens(edit.word_edits, edit.new_text or "")
    return colorize(f"+{text}", GREEN, enabled=color)

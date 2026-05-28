"""Shared helpers for diff-tool tests."""

from __future__ import annotations

from diff_tool.models import Operation


def apply_edit_script(edits) -> list[str | None]:
    output: list[str | None] = []
    for edit in edits:
        if edit.op is Operation.EQUAL:
            output.append(edit.new_text)
        elif edit.op is Operation.INSERT:
            output.append(edit.new_text)
    return output

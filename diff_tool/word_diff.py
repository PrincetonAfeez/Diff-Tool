"""Optional token-level diff built on the same LCS implementation."""

from __future__ import annotations

from diff_tool.lcs import lcs_steps
from diff_tool.models import Operation, TokenEdit


def diff_tokens(
    old_text: str,
    new_text: str,
    *,
    max_table_cells: int | None = None,
) -> tuple[TokenEdit, ...]:
    old_tokens = old_text.split()
    new_tokens = new_text.split()
    steps = lcs_steps(old_tokens, new_tokens, max_cells=max_table_cells)
    edits: list[TokenEdit] = []

    for op, old_index, new_index in steps:
        if op is Operation.EQUAL:
            assert old_index is not None and new_index is not None
            edits.append(
                TokenEdit(
                    op=Operation.EQUAL,
                    old_token=old_tokens[old_index],
                    new_token=new_tokens[new_index],
                )
            )
        elif op is Operation.DELETE:
            assert old_index is not None
            edits.append(
                TokenEdit(op=Operation.DELETE, old_token=old_tokens[old_index])
            )
        else:
            assert new_index is not None
            edits.append(
                TokenEdit(op=Operation.INSERT, new_token=new_tokens[new_index])
            )

    return tuple(edits)


def render_deleted_tokens(word_edits: tuple[TokenEdit, ...], fallback: str) -> str:
    if not word_edits:
        return fallback

    parts: list[str] = []
    for edit in word_edits:
        if edit.op is Operation.EQUAL and edit.old_token is not None:
            parts.append(edit.old_token)
        elif edit.op is Operation.DELETE and edit.old_token is not None:
            parts.append(f"[-{edit.old_token}-]")
    return " ".join(parts)


def render_inserted_tokens(word_edits: tuple[TokenEdit, ...], fallback: str) -> str:
    if not word_edits:
        return fallback

    parts: list[str] = []
    for edit in word_edits:
        if edit.op is Operation.EQUAL and edit.new_token is not None:
            parts.append(edit.new_token)
        elif edit.op is Operation.INSERT and edit.new_token is not None:
            parts.append(f"{{+{edit.new_token}+}}")
    return " ".join(parts)

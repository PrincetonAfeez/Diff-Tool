"""Pure diff engine that coordinates normalization, LCS, hunks, and stats."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from diff_tool.errors import InvalidOptionError
from diff_tool.hunks import build_hunks
from diff_tool.lcs import BacktraceStep, lcs_steps
from diff_tool.models import DiffOptions, DiffResult, Edit, Operation
from diff_tool.normalize import PreparedLine, prepare_lines
from diff_tool.stats import calculate_stats
from diff_tool.word_diff import diff_tokens


def diff_lines(
    old_lines: list[str],
    new_lines: list[str],
    options: DiffOptions | None = None,
) -> DiffResult:
    options = options or DiffOptions()
    if options.context_lines < 0:
        raise InvalidOptionError("context_lines must be zero or greater")
    if options.max_table_cells < 1:
        raise InvalidOptionError("max_table_cells must be at least 1")

    old_prepared = prepare_lines(old_lines, options)
    new_prepared = prepare_lines(new_lines, options)
    old_keys = [line.key for line in old_prepared]
    new_keys = [line.key for line in new_prepared]

    steps = lcs_steps(old_keys, new_keys, max_cells=options.max_table_cells)
    edits = _steps_to_edits(steps, old_prepared, new_prepared)

    if options.word_diff:
        edits = _add_word_diffs(edits, max_table_cells=options.max_table_cells)

    hunks = build_hunks(edits, context_lines=options.context_lines)
    stats = calculate_stats(
        edits,
        old_line_count=len(old_lines),
        new_line_count=len(new_lines),
    )

    return DiffResult(
        edits=tuple(edits),
        hunks=tuple(hunks),
        stats=stats,
        options=options,
        old_line_count=len(old_lines),
        new_line_count=len(new_lines),
    )


def _steps_to_edits(
    steps: Sequence[BacktraceStep],
    old_prepared: Sequence[PreparedLine],
    new_prepared: Sequence[PreparedLine],
) -> list[Edit]:
    edits: list[Edit] = []

    for op, old_pos, new_pos in steps:
        if op is Operation.EQUAL:
            assert old_pos is not None and new_pos is not None
            old_line = old_prepared[old_pos]
            new_line = new_prepared[new_pos]
            edits.append(
                Edit(
                    op=Operation.EQUAL,
                    old_index=old_line.index,
                    new_index=new_line.index,
                    old_line_no=old_line.line_no,
                    new_line_no=new_line.line_no,
                    old_text=old_line.text,
                    new_text=new_line.text,
                    old_key=old_line.key,
                    new_key=new_line.key,
                )
            )
        elif op is Operation.DELETE:
            assert old_pos is not None
            old_line = old_prepared[old_pos]
            edits.append(
                Edit(
                    op=Operation.DELETE,
                    old_index=old_line.index,
                    old_line_no=old_line.line_no,
                    old_text=old_line.text,
                    old_key=old_line.key,
                )
            )
        else:
            assert new_pos is not None
            new_line = new_prepared[new_pos]
            edits.append(
                Edit(
                    op=Operation.INSERT,
                    new_index=new_line.index,
                    new_line_no=new_line.line_no,
                    new_text=new_line.text,
                    new_key=new_line.key,
                )
            )

    return edits


def _add_word_diffs(edits: list[Edit], *, max_table_cells: int) -> list[Edit]:
    """Pair consecutive delete/insert blocks line-by-line for token diffs."""

    updated = list(edits)
    index = 0

    while index < len(updated):
        if updated[index].op is not Operation.DELETE:
            index += 1
            continue

        delete_start = index
        while index < len(updated) and updated[index].op is Operation.DELETE:
            index += 1

        insert_start = index
        while index < len(updated) and updated[index].op is Operation.INSERT:
            index += 1

        pair_count = min(insert_start - delete_start, index - insert_start)
        for offset in range(pair_count):
            delete_edit = updated[delete_start + offset]
            insert_edit = updated[insert_start + offset]
            if delete_edit.old_text is None or insert_edit.new_text is None:
                continue
            token_edits = diff_tokens(
                delete_edit.old_text,
                insert_edit.new_text,
                max_table_cells=max_table_cells,
            )
            updated[delete_start + offset] = replace(
                delete_edit, word_edits=token_edits
            )
            updated[insert_start + offset] = replace(
                insert_edit, word_edits=token_edits
            )

    return updated

"""Summary statistics for edit scripts."""

from __future__ import annotations

from diff_tool.models import DiffStats, Edit, Operation


def calculate_stats(
    edits: list[Edit],
    *,
    old_line_count: int,
    new_line_count: int,
) -> DiffStats:
    equal_count = sum(1 for edit in edits if edit.op is Operation.EQUAL)
    insert_count = sum(1 for edit in edits if edit.op is Operation.INSERT)
    delete_count = sum(1 for edit in edits if edit.op is Operation.DELETE)
    changed_count = _count_changed_lines(edits)

    comparable_old_count = equal_count + delete_count
    comparable_new_count = equal_count + insert_count
    denominator = max(comparable_old_count, comparable_new_count)
    similarity = 100.0 if denominator == 0 else (equal_count / denominator) * 100

    return DiffStats(
        old_line_count=old_line_count,
        new_line_count=new_line_count,
        equal_count=equal_count,
        insert_count=insert_count,
        delete_count=delete_count,
        changed_count=changed_count,
        similarity=round(similarity, 2),
    )


def _count_changed_lines(edits: list[Edit]) -> int:
    """Count non-equal runs as max(deletes, inserts) within each run."""

    total = 0
    index = 0

    while index < len(edits):
        if edits[index].op is Operation.EQUAL:
            index += 1
            continue

        deletes = 0
        inserts = 0
        while index < len(edits) and edits[index].op is not Operation.EQUAL:
            if edits[index].op is Operation.DELETE:
                deletes += 1
            elif edits[index].op is Operation.INSERT:
                inserts += 1
            index += 1

        total += max(deletes, inserts)

    return total

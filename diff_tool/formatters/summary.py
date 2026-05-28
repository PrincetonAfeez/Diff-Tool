"""Summary/stat formatter."""

from __future__ import annotations

from diff_tool.models import DiffResult


def format_summary(result: DiffResult) -> str:
    stats = result.stats
    status = "different" if result.has_changes else "identical"
    return "\n".join(
        [
            f"Status: {status}",
            f"Old lines: {stats.old_line_count}",
            f"New lines: {stats.new_line_count}",
            f"Equal lines: {stats.equal_count}",
            f"Inserted lines: +{stats.insert_count}",
            f"Deleted lines: -{stats.delete_count}",
            f"Changed lines: {stats.changed_count}",
            f"Similarity: {stats.similarity:.2f}%",
        ]
    )

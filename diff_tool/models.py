"""Dataclasses and enums shared by the diff engine and formatters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Operation(str, Enum):
    EQUAL = "equal"
    INSERT = "insert"
    DELETE = "delete"


@dataclass(frozen=True)
class TokenEdit:
    op: Operation
    old_token: str | None = None
    new_token: str | None = None


@dataclass(frozen=True)
class Edit:
    op: Operation
    old_index: int | None = None
    new_index: int | None = None
    old_line_no: int | None = None
    new_line_no: int | None = None
    old_text: str | None = None
    new_text: str | None = None
    old_key: str | None = None
    new_key: str | None = None
    word_edits: tuple[TokenEdit, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    edits: tuple[Edit, ...]


@dataclass(frozen=True)
class DiffOptions:
    ignore_trailing_space: bool = False
    ignore_all_space: bool = False
    ignore_blank_lines: bool = False
    ignore_case: bool = False
    context_lines: int = 3
    word_diff: bool = False
    max_table_cells: int = 2_000_000


@dataclass(frozen=True)
class DiffStats:
    old_line_count: int
    new_line_count: int
    equal_count: int
    insert_count: int
    delete_count: int
    changed_count: int
    similarity: float


@dataclass(frozen=True)
class FileInput:
    label: str
    lines: list[str]
    line_endings: tuple[str, ...] = ()

    @property
    def mixed_line_endings(self) -> bool:
        return len(set(self.line_endings)) > 1


@dataclass(frozen=True)
class DiffResult:
    edits: tuple[Edit, ...]
    hunks: tuple[Hunk, ...]
    stats: DiffStats
    options: DiffOptions
    old_line_count: int
    new_line_count: int

    @property
    def has_changes(self) -> bool:
        return self.stats.insert_count > 0 or self.stats.delete_count > 0

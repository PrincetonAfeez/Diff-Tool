"""Comparison normalization that preserves original display text."""

from __future__ import annotations

from dataclasses import dataclass

from diff_tool.models import DiffOptions


@dataclass(frozen=True)
class PreparedLine:
    index: int
    line_no: int
    text: str
    key: str


def normalize_line(line: str, options: DiffOptions) -> str:
    key = line
    if options.ignore_trailing_space:
        key = key.rstrip()
    if options.ignore_all_space:
        key = "".join(key.split())
    if options.ignore_case:
        key = key.casefold()
    return key


def prepare_lines(lines: list[str], options: DiffOptions) -> list[PreparedLine]:
    prepared: list[PreparedLine] = []

    for index, line in enumerate(lines):
        key = normalize_line(line, options)
        if options.ignore_blank_lines and line.strip() == "":
            continue
        prepared.append(
            PreparedLine(
                index=index,
                line_no=index + 1,
                text=line,
                key=key,
            )
        )

    return prepared

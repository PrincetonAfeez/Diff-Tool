"""Input reading, binary detection, UTF-8 decoding, and line-ending metadata."""

from __future__ import annotations

import re
from pathlib import Path

from diff_tool.errors import BinaryFileError, EncodingError, InputError
from diff_tool.models import FileInput

LINE_ENDING_RE = re.compile(r"\r\n|\r|\n")


def read_input(path: str, *, stdin_text: str | None = None) -> FileInput:
    if path == "-":
        if stdin_text is None:
            raise InputError("stdin input was requested but no stdin text was provided")
        return input_from_text("stdin", stdin_text)

    file_path = Path(path)
    try:
        data = file_path.read_bytes()
    except FileNotFoundError as exc:
        raise InputError(f"file not found: {path}") from exc
    except PermissionError as exc:
        raise InputError(f"permission denied: {path}") from exc
    except OSError as exc:
        raise InputError(f"could not read {path}: {exc}") from exc

    if looks_binary(data):
        raise BinaryFileError(f"binary files are not supported: {path}")

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EncodingError(f"could not decode {path} as UTF-8") from exc

    return input_from_text(path, text)


def input_from_text(label: str, text: str) -> FileInput:
    endings = tuple(match.group(0) for match in LINE_ENDING_RE.finditer(text))
    return FileInput(label=label, lines=text.splitlines(), line_endings=endings)


def looks_binary(data: bytes) -> bool:
    return b"\x00" in data[:4096]

"""Tests for the input reading, binary detection, UTF-8 decoding, and line-ending metadata."""

from pathlib import Path

import pytest

from diff_tool.errors import BinaryFileError, EncodingError, InputError
from diff_tool.io import input_from_text, looks_binary, read_input


def test_read_input_decodes_utf8_and_splits_lines(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"a\nb\n")

    file_input = read_input(str(path))

    assert file_input.lines == ["a", "b"]
    assert file_input.line_endings == ("\n", "\n")


def test_read_input_detects_mixed_line_endings(tmp_path):
    path = tmp_path / "mixed.txt"
    path.write_bytes(b"a\r\nb\n")

    file_input = read_input(str(path))

    assert file_input.mixed_line_endings


def test_read_input_rejects_binary_file(tmp_path):
    path = tmp_path / "image.bin"
    path.write_bytes(b"a\x00b")

    with pytest.raises(BinaryFileError):
        read_input(str(path))


def test_read_input_rejects_invalid_utf8(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff")

    with pytest.raises(EncodingError):
        read_input(str(path))


def test_read_input_missing_file_is_input_error(tmp_path):
    with pytest.raises(InputError):
        read_input(str(tmp_path / "missing.txt"))


def test_read_input_stdin_without_text_raises_input_error():
    with pytest.raises(InputError):
        read_input("-")


def test_read_input_stdin_with_text():
    file_input = read_input("-", stdin_text="a\nb\n")

    assert file_input.label == "stdin"
    assert file_input.lines == ["a", "b"]


def test_input_from_text_records_line_endings():
    file_input = input_from_text("sample", "a\r\nb\n")

    assert file_input.lines == ["a", "b"]
    assert file_input.mixed_line_endings


def test_looks_binary_detects_null_byte():
    assert looks_binary(b"text\x00more")
    assert not looks_binary(b"plain text")
    assert not looks_binary(b"")


def test_looks_binary_only_checks_first_chunk():
    data = b"x" * 5000 + b"\x00"
    assert not looks_binary(data)


def test_input_from_text_lf_only_not_mixed():
    file_input = input_from_text("f", "a\nb\n")

    assert not file_input.mixed_line_endings
    assert file_input.line_endings == ("\n", "\n")


def test_read_input_permission_denied(tmp_path, monkeypatch):
    path = tmp_path / "secret.txt"
    path.write_text("x", encoding="utf-8")

    def raise_permission(self):
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "read_bytes", raise_permission)

    with pytest.raises(InputError, match="permission denied"):
        read_input(str(path))


def test_read_input_os_error(tmp_path, monkeypatch):
    path = tmp_path / "bad.txt"
    path.write_text("x", encoding="utf-8")

    def raise_os(self):
        raise OSError("device error")

    monkeypatch.setattr(Path, "read_bytes", raise_os)

    with pytest.raises(InputError, match="could not read"):
        read_input(str(path))

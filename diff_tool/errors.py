"""Structured errors for the diff tool."""


class DiffToolError(Exception):
    """Base class for expected diff-tool errors."""


class InputError(DiffToolError):
    """Raised when an input cannot be read or used."""


class EncodingError(DiffToolError):
    """Raised when input cannot be decoded as UTF-8."""


class BinaryFileError(DiffToolError):
    """Raised when an input looks like a binary file."""


class DiffAlgorithmError(DiffToolError):
    """Raised when the diff algorithm cannot process the input."""


class InvalidOptionError(DiffToolError):
    """Raised when diff options are invalid."""


class CLIError(DiffToolError):
    """Raised for expected CLI usage errors."""

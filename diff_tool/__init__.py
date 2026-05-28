"""Pure-Python LCS-based diff library."""

from diff_tool.engine import diff_lines
from diff_tool.errors import (
    BinaryFileError,
    CLIError,
    DiffAlgorithmError,
    DiffToolError,
    EncodingError,
    InputError,
    InvalidOptionError,
)
from diff_tool.models import DiffOptions, DiffResult, Edit, Hunk, Operation

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "BinaryFileError",
    "CLIError",
    "DiffAlgorithmError",
    "DiffOptions",
    "DiffResult",
    "DiffToolError",
    "Edit",
    "EncodingError",
    "Hunk",
    "InputError",
    "InvalidOptionError",
    "Operation",
    "diff_lines",
]

"""Exception hierarchy smoke tests """

from diff_tool.errors import (
    BinaryFileError,
    CLIError,
    DiffAlgorithmError,
    DiffToolError,
    EncodingError,
    InputError,
    InvalidOptionError,
)


def test_all_errors_inherit_from_diff_tool_error():
    for exc_type in (
        InputError,
        EncodingError,
        BinaryFileError,
        DiffAlgorithmError,
        InvalidOptionError,
        CLIError,
    ):
        assert issubclass(exc_type, DiffToolError)
        assert issubclass(exc_type, Exception)

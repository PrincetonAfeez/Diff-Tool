"""Public package surface."""

import diff_tool


def test_package_version():
    assert diff_tool.__version__ == "0.1.0"


def test_package_exports_diff_lines():
    assert diff_tool.diff_lines is not None
    assert "diff_lines" in diff_tool.__all__


def test_package_exports_errors_and_models():
    for name in (
        "DiffToolError",
        "InputError",
        "DiffOptions",
        "DiffResult",
        "Edit",
        "Operation",
    ):
        assert name in diff_tool.__all__
        assert hasattr(diff_tool, name)

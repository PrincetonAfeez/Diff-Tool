# Diff Tool

[![CI](https://github.com/PrincetonAfeez/Diff-Tool/actions/workflows/ci.yml/badge.svg)](https://github.com/PrincetonAfeez/Diff-Tool/actions/workflows/ci.yml)

A pure-Python text diff library and command-line tool built around the classic
Longest Common Subsequence algorithm.

The project intentionally implements the LCS dynamic-programming table by hand.
It does not use `difflib`, Hirschberg, Myers diff, or an external diff library.

## Features

- Library API for comparing two lists of lines
- `argparse` CLI
- Classic `O(n x m)` LCS table with backtrace
- Edit script using `EQUAL`, `DELETE`, and `INSERT`
- Unified, inline, side-by-side, and summary output
- Configurable unified context lines
- UTF-8 input with clean decode errors
- Simple binary-file detection (first 4 KiB scanned for NUL bytes)
- One-sided stdin using `-`
- Exit codes: `0` identical, `1` different, `2` error
- Optional comparison flags for whitespace and case
- Optional word-level diff for paired delete/insert lines

## Usage

```powershell
python -m diff_tool.cli old.txt new.txt
python -m diff_tool.cli old.txt new.txt --format summary
python -m diff_tool.cli old.txt new.txt --stat
python -m diff_tool.cli old.txt new.txt --format side-by-side --width 120
python -m diff_tool.cli old.txt new.txt --ignore-case
python -m diff_tool.cli old.txt new.txt --ignore-trailing-space
Get-Content old.txt | python -m diff_tool.cli - new.txt
```

If installed as a package, the console script is:

```powershell
pip install -e .
diff-tool old.txt new.txt
```

### CLI flags

| Flag | Description |
|------|-------------|
| `--version` | Print version and exit |
| `--format` | `unified`, `side-by-side`, `inline`, or `summary` |
| `--stat` | Shortcut for summary output |
| `-U`, `--context` | Unified context lines (default: 3) |
| `--ignore-trailing-space` | Ignore trailing whitespace when comparing |
| `--ignore-all-space` | Collapse all whitespace when comparing |
| `--ignore-blank-lines` | Skip blank lines during comparison and output |
| `--ignore-case` | Case-insensitive comparison |
| `--word-diff` | Token-level highlights for paired changed lines |
| `--color` | `auto`, `always`, or `never` |
| `--no-color` | Disable ANSI color |
| `--width` | Side-by-side total width (minimum 40) |

The hidden `--max-table-cells` guard rejects inputs that would allocate an
oversized DP table. Values below `1` are rejected.

## Examples

Sample files in `examples/` demonstrate a small text change:

```powershell
python -m diff_tool.cli examples/old.txt examples/new.txt
python -m diff_tool.cli examples/old.txt examples/new.txt --word-diff
```

## Library Example

```python
from diff_tool import diff_lines
from diff_tool.models import DiffOptions

result = diff_lines(
    ["The quick brown fox"],
    ["The quick red fox"],
    DiffOptions(word_diff=True),
)

for edit in result.edits:
    print(edit.op, edit.old_text, edit.new_text)
```

## Algorithm

Given sequences of length `n` and `m`, the engine builds a DP table where:

```text
table[i][j] = LCS length of prefixes a[:i] and b[:j]
```

Matching items extend the diagonal; mismatches take the row/column maximum.
Backtrace recovers an edit script of `EQUAL`, `DELETE`, and `INSERT` steps.

- **Time:** `O(n x m)`
- **Space:** `O(n x m)` for the full table
- **Tie-breaking:** documented in [ADR 0001](docs/adr/0001-plain-lcs-dp-table.md)

## Display Semantics

Formatters render the **edit script**, not a verbatim replay of both files.
See [ADR 0006](docs/adr/0006-display-and-word-diff-policy.md) for the full policy.

### Identical inputs

| Format | Output when files match | Exit code |
|--------|-------------------------|-----------|
| `unified` (default) | Empty string (silent) | `0` |
| `inline` / `side-by-side` | Full file with context prefixes | `0` |
| `summary` / `--stat` | Stats block (`Status: identical`) | `0` |

### Comparison flags and visible text

When lines compare equal under normalization flags, formatters show the **old
side text** (`old_text`) for EQUAL rows. This keeps output stable when
`--ignore-case` or `--ignore-trailing-space` is enabled. The underlying
`Edit` still stores both originals for library callers.

### Blank lines

With `--ignore-blank-lines`, blank lines are removed from the edit script.
They do **not** appear in unified, inline, or side-by-side output. Raw line
counts in summary stats still include those blank lines.

## Scope Boundaries

Version 1 is library + CLI only. A Django + HTMX showcase is intentionally not
part of this build. Very large files are also a non-goal because the selected
algorithm uses an `O(n x m)` table.

## Word Diff Limitations

Word diff applies only to **paired** delete/insert lines within a change block.
Consecutive deletes are paired with consecutive inserts in order; extra
unpaired lines are shown without token highlights.

Tokens are split on whitespace, so punctuation attached to a word (for example
`brown,`) is treated as part of that token.

Highlighted token output rejoins words with a **single space**, so spacing-only
changes may still appear as line-level delete/insert pairs without preserving
original gaps between words.

## Stats Definitions

- `old_line_count` / `new_line_count`: raw input line counts
- `insert_count`: number of `INSERT` operations in the edit script
- `delete_count`: number of `DELETE` operations
- `equal_count`: number of `EQUAL` operations
- `changed_count`: for each non-equal run, count `max(deletes, inserts)`
- `similarity`: `equal_count / max(comparable_old_count, comparable_new_count) * 100`

When `--ignore-blank-lines` is enabled, blank lines are omitted from comparison
and formatted output, but still appear in the raw line counts above. Similarity
is computed from the filtered edit script.

## Project Structure

```text
diff_tool/              Library and CLI (stdlib only)
  cli.py                argparse entry point and exit codes
  engine.py             normalize → LCS → hunks → stats → word diff
  lcs.py                DP table and backtrace
  hunks.py              Context grouping for unified output
  normalize.py          Comparison keys vs display text
  word_diff.py          Token-level LCS for changed lines
  io.py                 UTF-8 files, stdin, binary detection
  formatters/           unified, inline, side-by-side, summary
tests/                  Pytest suite (145 tests, ~100% coverage)
  conftest.py           Shared helpers
  test_*.py             Layer tests (LCS, engine, formatters, CLI, …)
  fixtures/             Golden expected outputs
docs/adr/               Architecture decision records
examples/               Sample inputs (old.txt, new.txt)
```

## Testing

The suite exercises the library and CLI by layer: LCS table and backtrace,
normalization, hunks, stats, word diff, all formatters, I/O errors, and
integration examples with golden unified output.

```powershell
pip install -e ".[dev]"
python -m pytest
python -m pytest --cov=diff_tool --cov-report=term-missing
```

Coverage is enforced at **95%** minimum on `diff_tool/` (currently ~100% on
library modules; the CLI `__main__` guard is excluded). CI runs the same
pytest + coverage command on Python 3.11–3.13.

| Test module | Focus |
|-------------|--------|
| `test_lcs.py`, `test_backtrace.py` | DP table, `lcs_steps`, direct backtrace |
| `test_engine.py` | `diff_lines`, options, reconstruction property |
| `test_normalize_and_color.py` | Keys, ANSI color policy |
| `test_hunks.py`, `test_hunks_stats.py` | Hunk merge/split, stats formulas |
| `test_word_diff.py` | Token diff and render markers |
| `test_formatters.py` | All output formats and color |
| `test_io.py` | Files, stdin, encoding, binary |
| `test_cli.py` | Exit codes, flags, errors |
| `test_examples.py` | `examples/` + golden fixture |
| `test_models.py`, `test_errors.py`, `test_package.py` | API surface |

## Development

Install editable with dev tools:

```powershell
pip install -e ".[dev]"
# or
pip install -r requirements-dev.txt
```

Runtime install has **no** third-party dependencies (`requirements.txt` is
documentation only). Dev dependencies are defined in `pyproject.toml`
under `[project.optional-dependencies.dev]` with floor and upper bounds
to reduce surprise CI breakage from major tool releases.

```powershell
python -m pytest
python -m pytest --cov=diff_tool --cov-report=term-missing
python -m ruff check .
python -m ruff format --check .
python -m mypy diff_tool
```

CI runs tests with coverage, ruff (check + format), and mypy on Python
3.11–3.13. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).

# Architecture Decision Record
## App — Diff Tool
**Text Infrastructure Group | Document 1 of 5**
**Status: Accepted**

---

## Context

The Text Infrastructure group requires a pure-Python text diff library and command-line tool. The project must compare two text inputs, identify equal/deleted/inserted lines, and render the result in formats useful for a terminal workflow. The implementation is intentionally algorithmic: it builds the Longest Common Subsequence dynamic-programming table by hand instead of delegating to `difflib`, Myers diff, Hirschberg, or an external diff package.

The app is scoped as a library plus CLI only. It is not a Django app, not a GUI, and not a version-control system. It is intended to demonstrate Python fundamentals, algorithm design, command-line interface discipline, packaging, typed dataclasses, testable formatters, and clear limits around performance.

The selected architecture separates comparison from presentation:
- normalize inputs into comparison keys
- run LCS on those keys
- backtrace the table into an edit script
- convert steps into typed `Edit` records
- optionally attach token-level word diffs
- group edits into hunks
- compute stats
- render through formatters

---

## Decisions

### Decision 1 — Implement plain LCS dynamic programming by hand

**Chosen:** Use a classic `O(n x m)` LCS table and backtrace.

**Rejected:** `difflib`, Myers diff, Hirschberg, Patience diff, or a third-party diff package.

**Reason:** The project is meant to demonstrate the algorithm. The full DP table is simple to inspect, teach, and test. This choice makes the trade-off obvious: excellent clarity for small/medium files, but poor memory scaling for very large inputs.

---

### Decision 2 — Use only `EQUAL`, `DELETE`, and `INSERT`

**Chosen:** The edit script uses three operations:
- `EQUAL`
- `DELETE`
- `INSERT`

**Rejected:** A separate `REPLACE` operation.

**Reason:** LCS naturally produces equality plus insert/delete changes. A replacement can be represented as a delete followed by an insert. Avoiding `REPLACE` keeps the engine simple and lets formatters decide how to present paired delete/insert lines.

---

### Decision 3 — Deterministic LCS tie-breaking

**Chosen:** During backtrace, when the DP scores tie, choose `INSERT` first. After reversal, the forward edit script favors `DELETE` before `INSERT` for single-line replacements.

**Rejected:** Arbitrary or implementation-dependent tie behavior.

**Reason:** Duplicate-line alignment is not unique. A deterministic rule makes tests stable and makes behavior explainable. The result is one valid LCS optimum, not a guarantee of the only possible alignment.

---

### Decision 4 — Separate comparison keys from display text

**Chosen:** Each prepared line stores both the original text and a normalized comparison key.

**Rejected:** Mutating input text before display or comparing raw text only.

**Reason:** Flags like `--ignore-case`, `--ignore-trailing-space`, and `--ignore-all-space` should affect comparison without erasing the original text that library callers may need. This also allows formatters to display stable text while still respecting comparison rules.

---

### Decision 5 — Remove blank lines from the edit script when ignored

**Chosen:** `--ignore-blank-lines` filters blank lines out of the comparison and formatted edit script.

**Rejected:** Keeping blank lines in output while ignoring them for matching.

**Reason:** A filtered edit script is easier to reason about. It means ignored blank lines do not appear in unified, inline, or side-by-side output. Raw line counts still appear in summary stats.

---

### Decision 6 — Keep formatters as presentation-only modules

**Chosen:** Formatters render `DiffResult` and do not recompute differences.

**Rejected:** Each formatter having its own comparison behavior.

**Reason:** One engine should define the diff. Formatters should only choose how to display that edit script. This prevents output modes from disagreeing about what changed.

---

### Decision 7 — Use unified output as the default

**Chosen:** Default CLI format is `unified`.

**Rejected:** Defaulting to inline, side-by-side, or summary.

**Reason:** Unified diff is the most familiar terminal format for developers. It is compact because it uses hunks and context lines. It is also the best format for golden-output tests.

---

### Decision 8 — Silent unified output for identical files

**Chosen:** Unified output returns an empty string when inputs are identical. Exit code remains `0`.

**Rejected:** Printing an "identical" message in unified mode.

**Reason:** This matches common command-line diff expectations. The summary formatter exists for users who want explicit identical/different status output.

---

### Decision 9 — Optional word diff as display enhancement

**Chosen:** `--word-diff` pairs consecutive delete/insert lines and runs token-level LCS using `str.split()`.

**Rejected:** Full intra-line diff engine with punctuation-aware tokenization and whitespace preservation.

**Reason:** Word diff is a helpful presentation layer, not the core algorithm. Keeping tokenization simple avoids turning V1 into a full text-rendering engine. The trade-off is that punctuation remains attached to tokens and original spacing is not preserved inside word-diff output.

---

### Decision 10 — Add a DP table size guard

**Chosen:** `DiffOptions.max_table_cells` and hidden CLI flag `--max-table-cells` guard against allocating an oversized LCS table.

**Rejected:** Letting Python attempt allocation until memory failure.

**Reason:** Plain LCS has known `O(n x m)` space usage. A guard makes the limit explicit, testable, and user-friendly. Values below 1 are rejected.

---

### Decision 11 — Make the runtime package standard-library only

**Chosen:** The project has no runtime dependencies. Dev tools are optional dependencies.

**Rejected:** Pulling in third-party packages for CLI, color, formatting, or diffing.

**Reason:** The app is an academic algorithmic build. Standard-library-only runtime makes installation simple and reinforces that the core behavior is implemented directly.

---

### Decision 12 — Treat binary and non-UTF-8 input as expected errors

**Chosen:** Input reading detects NUL bytes in the first 4 KiB and decodes files as UTF-8. Binary and decode failures become structured expected errors.

**Rejected:** Best-effort binary diff or arbitrary encoding detection.

**Reason:** V1 is a text diff tool. Supporting arbitrary binary data and encoding detection would expand scope substantially. Clear failure messages are preferable to misleading output.

---

## Consequences

**Positive:**
- The core algorithm is visible and testable.
- The library API is usable independently of the CLI.
- Formatters are independent and easy to reason about.
- Normalization flags do not destroy original display text.
- The DP table guard makes a known algorithmic limit explicit.
- Standard-library runtime keeps packaging simple.
- Exit codes are predictable for shell usage.
- Word diff is available without complicating the core edit model.
- Tests can verify each layer separately.

**Negative / Trade-offs:**
- Very large files are a documented non-goal.
- Plain LCS uses `O(n x m)` memory.
- No `REPLACE` operation means formatters infer replacement-like display from delete/insert runs.
- Word diff does not preserve original intra-line whitespace.
- Tokenization is whitespace-based.
- Binary files and non-UTF-8 text are rejected.
- Unified output is empty for identical inputs, which can surprise users expecting a status message.
- The tool is not patch-compatible with every edge of GNU diff.

---

## Alternatives Not Explored

- Myers diff for better practical performance.
- Hirschberg for lower memory.
- Patience diff for more human-friendly alignment.
- Binary file diffing.
- Encoding autodetection.
- JSON output.
- Directory recursive diff.
- Patch application.
- HTML rendering.
- GUI or web interface.

---

*Constitution reference: Article 1 (Python fundamentals and architectural thinking), Article 3.3 (scope discipline), Article 4 (quality proportional to scope), Article 6 (behavior verification), and Article 7 (progressive complexity).*

---


# Technical Design Document
## App — Diff Tool
**Text Infrastructure Group | Document 2 of 5**

---

## Overview

Diff Tool is a pure-Python text comparison package and CLI. It compares two line sequences, builds an LCS table, backtraces an edit script, groups changes into hunks, calculates summary stats, and renders output in unified, inline, side-by-side, or summary format.

**Package:** `diff_tool`  
**Console script:** `diff-tool`  
**Module CLI:** `python -m diff_tool.cli`  
**Python requirement:** `>=3.11`  
**Runtime dependencies:** none  
**Dev dependencies:** pytest, pytest-cov, ruff, mypy  
**Primary algorithm:** classic `O(n x m)` Longest Common Subsequence  
**Primary public API:** `diff_tool.diff_lines`

---

## Data Flow

### CLI flow

```text
User command
  │
  ▼
diff_tool.cli.build_parser()
  │
  ▼
argparse parses old/new paths and flags
  │
  ▼
validate CLI constraints
  ├── both inputs cannot be "-"
  ├── context >= 0
  ├── width >= 40
  └── max_table_cells >= 1
  │
  ▼
read_input()
  ├── file bytes or one-sided stdin
  ├── binary NUL check
  ├── UTF-8 decode
  └── line split + line-ending metadata
  │
  ▼
DiffOptions
  │
  ▼
diff_lines()
  │
  ▼
formatter selected by --format or --stat
  │
  ▼
stdout output
  │
  ├── exit 0 if identical
  ├── exit 1 if different
  └── exit 2 on expected error
```

---

### Engine flow

```text
old_lines + new_lines + DiffOptions
  │
  ▼
prepare_lines()
  ├── keep original text
  ├── derive comparison key
  └── optionally skip blank lines
  │
  ▼
old_keys + new_keys
  │
  ▼
lcs_steps()
  ├── build_lcs_table()
  └── backtrace_lcs()
  │
  ▼
_steps_to_edits()
  │
  ▼
optional _add_word_diffs()
  │
  ▼
build_hunks()
  │
  ▼
calculate_stats()
  │
  ▼
DiffResult
```

---

## Module-Level Structure

```text
Diff-Tool/
  diff_tool/
    __init__.py
    cli.py
    color.py
    engine.py
    errors.py
    hunks.py
    io.py
    lcs.py
    models.py
    normalize.py
    stats.py
    word_diff.py
    formatters/
      __init__.py
      inline.py
      side_by_side.py
      summary.py
      unified.py
  tests/
    conftest.py
    fixtures/
    test_*.py
  docs/adr/
  examples/
  pyproject.toml
  requirements.txt
  requirements-dev.txt
  README.md
  CHANGELOG.md
  LICENSE
  .github/workflows/ci.yml
```

---

## Module Dependency Graph

```text
diff_tool.__init__
  ├── engine.diff_lines
  ├── errors
  └── models

cli.py
  ├── color.should_color
  ├── engine.diff_lines
  ├── errors
  ├── formatters
  ├── io.read_input
  └── models.DiffOptions

engine.py
  ├── hunks.build_hunks
  ├── lcs.lcs_steps
  ├── models
  ├── normalize.prepare_lines
  ├── stats.calculate_stats
  └── word_diff.diff_tokens

lcs.py
  ├── errors.DiffAlgorithmError
  └── models.Operation

normalize.py
  └── models.DiffOptions

hunks.py
  ├── errors.InvalidOptionError
  └── models.Edit / Hunk / Operation

stats.py
  └── models.DiffStats / Edit / Operation

word_diff.py
  ├── lcs.lcs_steps
  └── models.TokenEdit / Operation

io.py
  ├── pathlib.Path
  ├── errors
  └── models.FileInput

formatters/*
  ├── color.colorize
  ├── models.DiffResult / Edit / Operation
  └── word_diff render helpers
```

---

## Core Data Structures

### `Operation`

```python
class Operation(str, Enum):
    EQUAL = "equal"
    INSERT = "insert"
    DELETE = "delete"
```

Defines the operation vocabulary shared by the engine, token diff, stats, and formatters.

---

### `TokenEdit`

```python
@dataclass(frozen=True)
class TokenEdit:
    op: Operation
    old_token: str | None = None
    new_token: str | None = None
```

Represents one token-level word-diff step.

---

### `Edit`

```python
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
    word_edits: tuple[TokenEdit, ...] = ()
```

The central line-level edit record. It stores both original text and normalized comparison keys when available.

---

### `Hunk`

```python
@dataclass(frozen=True)
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    edits: tuple[Edit, ...]
```

Represents a context-bounded group of changes for unified output.

---

### `DiffOptions`

```python
@dataclass(frozen=True)
class DiffOptions:
    ignore_trailing_space: bool = False
    ignore_all_space: bool = False
    ignore_blank_lines: bool = False
    ignore_case: bool = False
    context_lines: int = 3
    word_diff: bool = False
    max_table_cells: int = 2_000_000
```

Configuration shared between CLI and library callers.

---

### `DiffStats`

```python
@dataclass(frozen=True)
class DiffStats:
    old_line_count: int
    new_line_count: int
    equal_count: int
    insert_count: int
    delete_count: int
    changed_count: int
    similarity: float
```

Summary data for `summary` and `--stat` output.

---

### `FileInput`

```python
@dataclass(frozen=True)
class FileInput:
    label: str
    lines: list[str]
    line_endings: tuple[str, ...] = ()
```

Input wrapper used by the CLI. It tracks mixed line endings.

---

### `DiffResult`

```python
@dataclass(frozen=True)
class DiffResult:
    edits: tuple[Edit, ...]
    hunks: tuple[Hunk, ...]
    stats: DiffStats
    options: DiffOptions
    old_line_count: int
    new_line_count: int
```

Main library result object.

Computed property:
```python
has_changes
```

Returns true when insert or delete count is non-zero.

---

### `PreparedLine`

```python
@dataclass(frozen=True)
class PreparedLine:
    index: int
    line_no: int
    text: str
    key: str
```

Internal normalized representation used by the engine before LCS.

---

## Function Reference

### `diff_lines(old_lines, new_lines, options=None)`

Main library API.

Responsibilities:
1. Validate `context_lines` and `max_table_cells`.
2. Normalize old/new lines into `PreparedLine` objects.
3. Extract comparison keys.
4. Run LCS.
5. Convert backtrace steps into `Edit` records.
6. Add optional word diffs.
7. Build hunks.
8. Calculate stats.
9. Return `DiffResult`.

---

### `build_lcs_table(a, b, max_cells=None)`

Builds the full LCS DP table.

Formula:
```text
table[i][j] = LCS length of a[:i] and b[:j]
```

Guard:
```text
(len(a) + 1) * (len(b) + 1) <= max_cells
```

Raises `DiffAlgorithmError` when the table would exceed the configured guard.

---

### `backtrace_lcs(a, b, table)`

Converts a completed LCS table into operation steps.

Tie policy:
- choose `INSERT` first on equal DP score during backward traversal
- after reversal, single-line replacements appear as `DELETE` before `INSERT`

---

### `lcs_steps(a, b, max_cells=None)`

Convenience wrapper:
```text
build_lcs_table() → backtrace_lcs()
```

---

### `normalize_line(line, options)`

Applies comparison-only transformations:
- trailing-space trim
- all-whitespace removal
- casefolding

---

### `prepare_lines(lines, options)`

Creates `PreparedLine` rows and optionally skips blank lines.

Important behavior:
- original text remains available for display
- normalized key is used for LCS
- raw line numbers are preserved

---

### `build_hunks(edits, context_lines=3)`

Finds changed edit indexes, expands each by context lines, merges overlapping ranges, and returns `Hunk` objects.

No changes:
```python
[]
```

Invalid context:
```text
InvalidOptionError
```

---

### `calculate_stats(edits, old_line_count, new_line_count)`

Calculates equal count, insert count, delete count, changed count by non-equal run, and similarity percentage.

`changed_count` uses:
```text
sum(max(deletes, inserts) for each non-equal run)
```

---

### `diff_tokens(old_text, new_text, max_table_cells=None)`

Splits both lines with `str.split()`, runs the same LCS implementation on tokens, and returns `TokenEdit` records.

---

### `read_input(path, stdin_text=None)`

Reads either a file path or one-sided stdin.

Behavior:
- `-` requires provided stdin text
- file not found, permission, and OS errors become `InputError`
- NUL byte in first 4096 bytes becomes `BinaryFileError`
- UTF-8 decode failure becomes `EncodingError`
- successful reads return `FileInput`

---

### Formatter functions

Public formatter functions:
- `format_unified(result, old_label="old", new_label="new", color=False)`
- `format_inline(result, color=False)`
- `format_side_by_side(result, width=100, color=False)`
- `format_summary(result)`

---

## Error Handling Strategy

Expected errors inherit from `DiffToolError`:
- `InputError`
- `EncodingError`
- `BinaryFileError`
- `DiffAlgorithmError`
- `InvalidOptionError`
- `CLIError`

CLI behavior:
- prints `error: ...` to stderr
- returns exit code `2`

---

## External Dependencies

### Runtime

None. The runtime package uses only the Python standard library.

### Development

Configured optional dev dependencies:
- pytest
- pytest-cov
- ruff
- mypy

---

## Concurrency Model

The app is synchronous and single-process. There is no async I/O, background worker, file watcher, parallel diff computation, or shared mutable state.

Each invocation reads both inputs, computes one `DiffResult`, prints output, and exits.

---

## Performance Characteristics

### LCS

Time:
```text
O(n x m)
```

Space:
```text
O(n x m)
```

where `n` is the old sequence length and `m` is the new sequence length.

### Word diff

For each paired delete/insert line pair:
```text
O(tokens_old x tokens_new)
```

### Guard

Default max table cells:
```text
2,000,000
```

This guard applies to line-level LCS and token-level word diff.

---

## Known Limitations

- Very large files are out of scope.
- No directory recursive diff.
- No binary diff.
- No automatic encoding detection.
- No patch apply.
- No JSON output.
- No `REPLACE` operation.
- Word diff tokenization is whitespace-only.
- Word diff does not preserve original spaces between tokens.
- Unified output does not print an identical-message banner.
- Side-by-side output clips long lines.
- `--ignore-blank-lines` removes blank lines from formatted output.

---

## Design Patterns Used

- **Functional core, imperative shell:** CLI handles process concerns; engine handles pure diff behavior.
- **Typed dataclass model:** immutable result records make outputs testable.
- **Strategy-style formatters:** one result object, multiple renderers.
- **Explicit error hierarchy:** expected failures avoid stack traces.
- **Normalization pipeline:** comparison key separated from display text.
- **Guardrail option:** known algorithmic limits surfaced as configuration.
- **Layered tests:** algorithm, engine, formatter, CLI, I/O, and packaging tested separately.

---

## Verification Summary

The repository documents tests across:
- LCS table and backtrace
- engine behavior
- normalization and color policy
- hunk construction
- stats formulas
- word diff
- unified, inline, side-by-side, and summary formatters
- file/stdin I/O
- encoding and binary errors
- CLI flags and exit codes
- examples and golden fixtures
- package API surface

CI runs pytest with coverage, Ruff check, Ruff format check, and mypy on supported Python versions.

---

*Constitution reference: Article 4 (engineering quality), Article 6 (behavior verification), Article 7 (progressive complexity), and Article 8 (valid learner work).*

---


# Interface Design Specification
## App — Diff Tool
**Text Infrastructure Group | Document 3 of 5**

---

## Public CLI Interface

### Module invocation

```powershell
python -m diff_tool.cli <old> <new> [options]
```

### Console script

```powershell
diff-tool <old> <new> [options]
```

### Version

```powershell
diff-tool --version
```

---

## Command Syntax

```text
diff-tool old new
diff-tool old new --format unified
diff-tool old new --format inline
diff-tool old new --format side-by-side --width 120
diff-tool old new --format summary
diff-tool old new --stat
diff-tool old new -U 5
diff-tool old new --ignore-case
diff-tool old new --ignore-trailing-space
diff-tool old new --ignore-all-space
diff-tool old new --ignore-blank-lines
diff-tool old new --word-diff
diff-tool old new --color auto
diff-tool old new --color always
diff-tool old new --color never
diff-tool old new --no-color
diff-tool - new
```

---

## Positional Arguments

| Argument | Required | Description |
|---|---:|---|
| `old` | Yes | Old file path, or `-` for stdin |
| `new` | Yes | New file path, or `-` for stdin |

Only one side may be stdin. Supplying `- -` is invalid.

---

## CLI Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--version` | flag | none | Prints package version and exits |
| `--format` | choice | `unified` | Output format: `unified`, `side-by-side`, `inline`, `summary` |
| `--stat` | flag | false | Shortcut for summary output |
| `-U`, `--context` | int | `3` | Unified context lines |
| `--ignore-trailing-space` | flag | false | Ignore trailing whitespace in comparison |
| `--ignore-all-space` | flag | false | Remove all whitespace from comparison keys |
| `--ignore-blank-lines` | flag | false | Remove blank lines from comparison and formatted edit output |
| `--ignore-case` | flag | false | Compare using `casefold()` |
| `--word-diff` | flag | false | Add token-level highlights to paired delete/insert lines |
| `--color` | choice | `auto` | `auto`, `always`, or `never` |
| `--no-color` | flag | false | Disable ANSI color |
| `--width` | int | `100` | Side-by-side total width |
| `--max-table-cells` | hidden int | `2_000_000` | Rejects oversized LCS tables |

---

## Validation Rules

| Condition | Result |
|---|---|
| both inputs are `-` | CLI error |
| `--context < 0` | CLI error |
| `--width < 40` | CLI error |
| `--max-table-cells < 1` | CLI error |
| file does not exist | input error |
| permission denied | input error |
| NUL byte in first 4096 bytes | binary-file error |
| UTF-8 decode failure | encoding error |
| DP table exceeds max cells | algorithm error |

Expected CLI errors return exit code `2`.

---

## Exit Codes

| Code | Meaning |
|---:|---|
| `0` | Inputs compare identical under selected options |
| `1` | Inputs differ under selected options |
| `2` | Expected error or broken pipe |

---

## Output Contracts

### Unified format

Identical inputs:
```text
<empty output>
```

Different inputs:
```text
--- old.txt
+++ new.txt
@@ -1,3 +1,3 @@
 unchanged
-deleted line
+inserted line
```

Properties:
- Uses hunks.
- Honors `--context`.
- Shows old/new labels from file paths or stdin label.
- Uses word-diff markers when enabled.
- Uses ANSI color when color policy enables it.

---

### Inline format

```text
  equal line
- deleted line
+ inserted line
```

Properties:
- Renders every edit, not just hunks.
- Prints full file even when identical.
- Uses old text for equal rows.
- Supports word-diff markers on changed paired lines.

---

### Side-by-side format

```text
old text                                      new text
deleted text                              <   
                                          > inserted text
```

Properties:
- Renders every edit.
- Uses a left and right column.
- Minimum total width is 40.
- Long lines are clipped with `...`.
- Equal rows display the old-side text on both sides when needed for stability.

---

### Summary format

```text
Status: different
Old lines: 10
New lines: 12
Equal lines: 8
Inserted lines: +3
Deleted lines: -1
Changed lines: 3
Similarity: 66.67%
```

Properties:
- `--stat` forces this output regardless of `--format`.
- Raw line counts include ignored blank lines.
- Similarity is computed from the filtered edit script.

---

## Library API Contract

### Import

```python
from diff_tool import diff_lines
from diff_tool.models import DiffOptions
```

or:

```python
from diff_tool import DiffOptions, Operation, DiffResult
```

---

### `diff_lines()`

Signature:

```python
def diff_lines(
    old_lines: list[str],
    new_lines: list[str],
    options: DiffOptions | None = None,
) -> DiffResult:
    ...
```

Inputs:
- `old_lines`: list of old-side lines without line endings
- `new_lines`: list of new-side lines without line endings
- `options`: optional `DiffOptions`

Output:
- `DiffResult`

Raises:
- `InvalidOptionError`
- `DiffAlgorithmError`

---

### `DiffOptions`

```python
DiffOptions(
    ignore_trailing_space=False,
    ignore_all_space=False,
    ignore_blank_lines=False,
    ignore_case=False,
    context_lines=3,
    word_diff=False,
    max_table_cells=2_000_000,
)
```

---

### `DiffResult`

Important fields:
- `edits`
- `hunks`
- `stats`
- `options`
- `old_line_count`
- `new_line_count`
- `has_changes`

---

### Public package exports

The package exports:
- `__version__`
- `diff_lines`
- `DiffOptions`
- `DiffResult`
- `Edit`
- `Hunk`
- `Operation`
- `DiffToolError`
- `InputError`
- `EncodingError`
- `BinaryFileError`
- `DiffAlgorithmError`
- `InvalidOptionError`
- `CLIError`

---

## Input Contract

### File input

Files must be:
- readable
- text
- decodable as UTF-8

Line splitting:
- uses `splitlines()`
- line-ending metadata is tracked separately for mixed-line-ending warnings

Binary detection:
- first 4096 bytes are scanned for NUL bytes

---

### Stdin input

`-` may be used for one side only:

```powershell
Get-Content old.txt | python -m diff_tool.cli - new.txt
```

Invalid:
```powershell
python -m diff_tool.cli - -
```

---

## Color Contract

### Modes

| Mode | Behavior |
|---|---|
| `auto` | color only when stdout looks like a TTY |
| `always` | force ANSI color |
| `never` | disable ANSI color |
| `--no-color` | disable ANSI color regardless of mode |
| `NO_COLOR` env var | disables ANSI color |

Colors:
- red for deletions
- green for insertions
- cyan for unified hunk headers

---

## Error Output Contract

Expected errors write to stderr:

```text
error: <message>
```

Examples:

```text
error: both inputs cannot be stdin
error: width must be at least 40
error: binary files are not supported: image.png
error: could not decode notes.txt as UTF-8
error: input is too large for the plain O(n x m) LCS table (...)
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `NO_COLOR` | Disables ANSI color output |

No other runtime environment variables are required.

---

## Configuration Files

### `pyproject.toml`

Defines package metadata, Python `>=3.11`, zero runtime dependencies, optional dev dependencies, console script, pytest config, coverage threshold, Ruff config, and mypy config.

### `requirements.txt`

Documentary runtime file. Runtime package has no third-party dependencies.

### `requirements-dev.txt`

Development dependency install path.

### `.github/workflows/ci.yml`

Runs pytest with coverage on Python 3.11, 3.12, and 3.13, then Ruff check, Ruff format check, and mypy.

---

## Side Effects

| Operation | Side Effect |
|---|---|
| CLI file read | Reads files from disk |
| CLI stdin input | Reads stdin once |
| CLI output | Writes formatted diff to stdout |
| CLI warning | Writes mixed-line-ending warning to stderr |
| CLI error | Writes expected error to stderr |
| Library `diff_lines()` | Pure in-memory operation; no file I/O |

The library API itself does not modify files.

---

## Usage Examples

### Basic unified diff

```powershell
python -m diff_tool.cli old.txt new.txt
```

---

### Summary only

```powershell
python -m diff_tool.cli old.txt new.txt --stat
```

---

### Side-by-side output

```powershell
python -m diff_tool.cli old.txt new.txt --format side-by-side --width 120
```

---

### Ignore case

```powershell
python -m diff_tool.cli old.txt new.txt --ignore-case
```

---

### Ignore trailing whitespace

```powershell
python -m diff_tool.cli old.txt new.txt --ignore-trailing-space
```

---

### Word diff

```powershell
python -m diff_tool.cli old.txt new.txt --word-diff
```

---

### One-sided stdin

```powershell
Get-Content old.txt | python -m diff_tool.cli - new.txt
```

---

### Library use

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

---

*Constitution reference: Article 4 (input/output boundaries), Article 6 (verification), and Article 8 (understandable and verifiable work).*

---


# Runbook
## App — Diff Tool
**Text Infrastructure Group | Document 4 of 5**

---

## Requirements

### Runtime

- Python 3.11 or newer
- No third-party runtime dependencies

### Development

- pytest
- pytest-cov
- ruff
- mypy

---

## Installation

### Editable install

```powershell
pip install -e .
```

### Editable install with dev dependencies

```powershell
pip install -e ".[dev]"
```

Alternative:

```powershell
pip install -r requirements-dev.txt
```

---

## Running the Tool

### Module invocation

```powershell
python -m diff_tool.cli old.txt new.txt
```

### Console script

```powershell
diff-tool old.txt new.txt
```

---

## Smoke Test

Create two files:

```powershell
Set-Content old.txt "alpha`nbeta`ngamma"
Set-Content new.txt "alpha`nBETA`ngamma"
python -m diff_tool.cli old.txt new.txt
```

Expected:
- stdout contains unified diff output
- exit code is `1`

Then run:

```powershell
python -m diff_tool.cli old.txt old.txt
```

Expected:
- stdout empty in unified mode
- exit code is `0`

---

## Running Tests

### Test suite

```powershell
python -m pytest
```

### Coverage

```powershell
python -m pytest --cov=diff_tool --cov-report=term-missing
```

Expected:
- coverage must stay at or above 95%

---

## Running Quality Checks

### Ruff check

```powershell
python -m ruff check .
```

### Ruff format check

```powershell
python -m ruff format --check .
```

### Mypy

```powershell
python -m mypy diff_tool
```

---

## Standard Operating Procedures

### Compare two files

```powershell
diff-tool old.txt new.txt
```

Use exit code:
- `0`: no difference
- `1`: difference
- `2`: error

---

### Produce summary stats

```powershell
diff-tool old.txt new.txt --stat
```

Use when a script needs a human-readable count instead of line-level diff.

---

### Compare while ignoring case

```powershell
diff-tool old.txt new.txt --ignore-case
```

---

### Compare while ignoring whitespace

Trailing whitespace only:

```powershell
diff-tool old.txt new.txt --ignore-trailing-space
```

All whitespace:

```powershell
diff-tool old.txt new.txt --ignore-all-space
```

Blank lines:

```powershell
diff-tool old.txt new.txt --ignore-blank-lines
```

---

### Use word-level highlights

```powershell
diff-tool old.txt new.txt --word-diff
```

Expected markers:
- deleted token: `[-token-]`
- inserted token: `{+token+}`

---

### Use side-by-side output

```powershell
diff-tool old.txt new.txt --format side-by-side --width 120
```

If output looks clipped, increase `--width`.

---

### Disable color

```powershell
diff-tool old.txt new.txt --no-color
```

or:

```powershell
$env:NO_COLOR = "1"
diff-tool old.txt new.txt
```

---

### Compare stdin to a file

```powershell
Get-Content old.txt | diff-tool - new.txt
```

Only one side can be stdin.

---

### Protect memory on large inputs

```powershell
diff-tool old.txt new.txt --max-table-cells 500000
```

This hidden guard rejects comparisons that would exceed the configured DP table size.

---

## Health Checks

### Package import

```powershell
python -c "from diff_tool import diff_lines; print(diff_lines(['a'], ['a']).has_changes)"
```

Expected:
```text
False
```

---

### Console entry point

```powershell
diff-tool --version
```

Expected:
```text
diff-tool 0.1.0
```

---

### Difference exit code

```powershell
python -m diff_tool.cli old.txt new.txt
```

Expected:
- `0` identical
- `1` different
- `2` error

---

### Formatter check

```powershell
python -m diff_tool.cli old.txt new.txt --format summary
python -m diff_tool.cli old.txt new.txt --format inline
python -m diff_tool.cli old.txt new.txt --format side-by-side
python -m diff_tool.cli old.txt new.txt --format unified
```

Expected:
- all commands complete
- only unified may be silent when inputs match

---

## Expected Output Samples

### Identical unified

```text
<empty stdout>
```

Exit:
```text
0
```

---

### Different unified

```text
--- old.txt
+++ new.txt
@@ -1,3 +1,3 @@
 alpha
-beta
+BETA
 gamma
```

Exit:
```text
1
```

---

### Summary

```text
Status: different
Old lines: 3
New lines: 3
Equal lines: 2
Inserted lines: +1
Deleted lines: -1
Changed lines: 1
Similarity: 66.67%
```

---

### Expected error

```text
error: both inputs cannot be stdin
```

Exit:
```text
2
```

---

## Known Failure Modes

### Oversized table

**Trigger:** Input sizes would allocate more than `max_table_cells`.

**Symptom:**
```text
error: input is too large for the plain O(n x m) LCS table (...)
```

**Resolution:**
- use smaller inputs
- raise `--max-table-cells` only if memory is acceptable
- use a different algorithm in a future version

---

### Binary input

**Trigger:** First 4096 bytes contain NUL.

**Symptom:**
```text
error: binary files are not supported: <path>
```

**Resolution:**
Use text files only.

---

### Non-UTF-8 input

**Trigger:** Input cannot decode as UTF-8.

**Symptom:**
```text
error: could not decode <path> as UTF-8
```

**Resolution:**
Convert file to UTF-8 before comparing.

---

### Both files passed as stdin

**Trigger:**
```powershell
diff-tool - -
```

**Symptom:**
```text
error: both inputs cannot be stdin
```

**Resolution:**
Use stdin for only one side.

---

### Width too small

**Trigger:**
```powershell
diff-tool old.txt new.txt --format side-by-side --width 20
```

**Symptom:**
```text
error: width must be at least 40
```

**Resolution:**
Use width 40 or greater.

---

### Negative context

**Trigger:**
```powershell
diff-tool old.txt new.txt -U -1
```

**Symptom:**
```text
error: context must be zero or greater
```

**Resolution:**
Use context 0 or greater.

---

### Mixed line endings warning

**Trigger:** A file contains more than one line-ending style.

**Symptom:**
```text
warning: mixed line endings detected in <label>
```

**Resolution:**
Normalize line endings if this matters for the workflow.

---

## Troubleshooting Decision Tree

```text
Command fails
  ├── Exit code 2?
  │   ├── Check stderr for expected error
  │   ├── Verify file paths
  │   ├── Verify UTF-8 text input
  │   ├── Verify only one side is stdin
  │   └── Verify table size guard
  ├── No output?
  │   ├── Are files identical under selected options?
  │   ├── Are you using unified format?
  │   └── Try --stat for explicit status
  ├── Output too wide or clipped?
  │   └── Increase --width for side-by-side
  ├── Color unexpected?
  │   ├── Check --color
  │   ├── Check --no-color
  │   └── Check NO_COLOR environment variable
  └── Word diff looks spacing-normalized?
      └── Expected: tokens are split and rejoined with one space
```

---

## Dependency Failure Handling

### Runtime import fails

Confirm install:

```powershell
pip install -e .
```

Then:

```powershell
python -c "import diff_tool; print(diff_tool.__version__)"
```

---

### Dev tools missing

Install dev dependencies:

```powershell
pip install -e ".[dev]"
```

---

### CI mismatch

Run the same local checks:

```powershell
python -m pytest --cov=diff_tool --cov-report=term-missing
python -m ruff check .
python -m ruff format --check .
python -m mypy diff_tool
```

---

## Recovery Procedures

### Recover from unexpected output

1. Run with `--stat` to confirm whether the engine sees changes.
2. Run with `--format inline` to inspect the full edit script.
3. Remove ignore flags to see raw comparison.
4. Disable color with `--no-color`.
5. Reduce input to a small reproduction.

---

### Recover from algorithm guard

1. Confirm line counts.
2. Estimate cells:
   ```text
   (old_lines + 1) * (new_lines + 1)
   ```
3. Use smaller files or split the comparison.
4. Raise `--max-table-cells` only when memory is acceptable.

---

### Recover from encoding issue

Convert the file to UTF-8, then rerun the diff.

---

## Maintenance Notes

- Keep the public `diff_lines()` API stable.
- Do not add `difflib` or an external diff engine without a new ADR.
- Keep formatter behavior tied to `DiffResult`, not raw file replay.
- Add tests before changing tie-breaking.
- Add tests before changing word-diff tokenization.
- Preserve exit-code contract for shell scripts.
- Keep runtime dependencies empty unless a new decision is documented.
- Keep `--max-table-cells` guard intact when changing the LCS implementation.
- If adding JSON output, define a stable schema first.
- If adding large-file support, consider Myers or Hirschberg and document the trade-off.

---

*Constitution reference: Article 6 (behavior verification), Article 5 (constraints and trade-offs), and Article 8 (verifiable learner work).*

---


# Lessons Learned
## App — Diff Tool
**Text Infrastructure Group | Document 5 of 5**

---

## Why This Design Was Chosen

This design was chosen because the purpose of the app is not merely to print a diff. The purpose is to demonstrate that the underlying comparison algorithm is understood and implemented directly. A wrapper around `difflib` would have produced useful output faster, but it would not prove mastery of the dynamic-programming idea.

The architecture keeps the learning target visible. `lcs.py` owns the DP table and backtrace. `engine.py` coordinates normalization, LCS, edits, hunks, stats, and word diff. Formatters only render the result. The CLI only handles user input, file I/O, color decisions, and exit codes.

That separation is important because diff tools can become tangled quickly. If comparison, formatting, and file reading live in one function, every new option becomes risky. Here, each option has a specific home.

---

## What Was Intentionally Omitted

**`difflib`:** Omitted because the goal is hand-built algorithmic understanding.

**Myers diff:** Omitted because it is more efficient but harder to teach and inspect.

**Hirschberg:** Omitted because reduced memory was less important than clarity.

**Binary diff:** Omitted because the app is explicitly a text diff.

**Encoding detection:** Omitted because UTF-8 only keeps behavior predictable.

**Directory diff:** Omitted to keep V1 focused on two text inputs.

**Patch application:** Out of scope.

**JSON output:** Deferred until a stable schema is designed.

**GUI/web interface:** Not part of the V1 scope.

---

## Biggest Weakness

The biggest weakness is algorithmic scalability. The full LCS table uses memory proportional to the product of the input lengths. This is fine for small and moderate text files, but it is not appropriate for very large files. The `max_table_cells` guard is honest about that limitation, but it does not solve it.

The second weakness is word-diff fidelity. Token-level LCS is useful, but `str.split()` tokenization means punctuation stays attached to words and original whitespace is not preserved. This keeps the code simple, but it limits exact visual fidelity.

The third weakness is that the tool does not implement a `REPLACE` operation. That decision keeps the model aligned with LCS, but it means replacement semantics are inferred by formatters from delete/insert pairs.

---

## Scaling Considerations

**If large-file support becomes important:**
- Replace or supplement plain LCS with Myers diff.
- Consider Hirschberg for lower memory.
- Add streaming/chunked comparison where possible.
- Preserve the existing simple engine as a reference mode.

**If richer word diff is needed:**
- Add punctuation-aware tokenization.
- Preserve whitespace tokens.
- Separate semantic tokens from render tokens.
- Add golden tests for spacing and punctuation.

**If JSON/API output is added:**
- Version the schema.
- Include operation, line numbers, original text, keys, and word edits.
- Avoid exposing unstable internal details.

**If directory diff is added:**
- Add path traversal, ignore rules, file matching, binary handling, and recursive summaries.
- Keep line diff as a reusable primitive.

---

## What the Next Refactor Would Be

1. **Introduce an algorithm interface** — allow `plain_lcs` now and possible `myers` later without rewriting formatters.

2. **Add JSON output** — expose `DiffResult` in a stable serialized form.

3. **Improve word tokenization** — preserve punctuation and spacing more carefully.

4. **Add performance benchmarks** — track memory/time behavior as input size grows.

5. **Add optional replace grouping** — keep the core edit operations but expose grouped change blocks for presentation.

---

## What This Project Taught

- **Algorithm choice shapes the whole product.** Plain LCS makes the implementation teachable but limits file size.

- **A diff is not just an algorithm.** It needs input handling, normalization, stats, display policy, exit codes, and error messages.

- **Display policy must be documented.** Equal rows under ignore flags can preserve different originals, so formatters need explicit rules.

- **Tie-breaking matters.** Duplicate lines create multiple valid LCS alignments. Tests need deterministic behavior.

- **Small CLI tools need contracts.** Exit codes, stderr behavior, stdin rules, and flags matter.

- **Standard-library-only is a design constraint.** It keeps the runtime clean and forces the implementation to own its behavior.

- **Tests become the specification.** The suite documents LCS, backtrace, normalization, hunks, stats, word diff, formatters, I/O, CLI, examples, and package exports.

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation), Article 6 (verification), and Article 7 (progressive complexity) for Diff Tool.*

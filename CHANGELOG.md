# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-28

### Added

- Hand-built LCS diff engine with `EQUAL`, `DELETE`, and `INSERT` operations
- Library API (`diff_lines`, `DiffOptions`, typed models)
- CLI with unified, inline, side-by-side, and summary output
- Comparison flags: trailing space, all space, blank lines, case
- Optional word-level diff for paired changed lines
- UTF-8 input, binary detection, stdin `-` support
- Six architecture decision records (ADRs)
- Pytest suite with examples integration and golden unified diff fixture
- GitHub Actions CI: tests, coverage, ruff, mypy
- MIT license

### Changed

- Word-diff pairing aligns consecutive delete/insert blocks line-by-line
- Side-by-side EQUAL rows show consistent old-side text under normalization flags
- `DiffResult.edits` and `.hunks` exposed as immutable tuples
- Validation uses `InvalidOptionError` / `CLIError` instead of bare `ValueError`

### Documented

- Display semantics for formatters, blank lines, and word-diff limits
- ADR 0006 for display text and word-diff policy
- Algorithm overview and scope boundaries in README

[0.1.0]: https://github.com/PrincetonAfeez/Diff-Tool/releases/tag/v0.1.0

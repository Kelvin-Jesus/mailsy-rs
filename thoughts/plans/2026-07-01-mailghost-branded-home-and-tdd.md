# Mailghost Branded Home — Manual Test-Writing Plan

## Purpose

The branded home screen is implemented. This document now contains only the
tests the learner will write by hand. Do not add production behavior while
following this plan unless a test exposes a real defect.

Tests should exercise the compiled `mailghost` binary and assert public CLI
behavior: exit status, stdout, and stderr. They should not import private
modules, inspect rendering helpers, mock internal code, or snapshot the entire
screen.

## Test Harness

When ready to begin:

1. Add `assert_cmd = "2.2.2"` under `[dev-dependencies]` in `Cargo.toml`.
2. Create `tests/home.rs`.
3. Run one test at a time:

   ```bash
   cargo test --test home <test_name> --locked -- --exact --nocapture
   ```

Because production behavior already exists, these are characterization and
regression tests rather than strict RED-first TDD. To prove that a test can
detect a regression, temporarily make one relevant production mutation,
observe the test fail, then restore the implementation and observe it pass.
Never commit the temporary mutation.

## Test 1 — Bare Invocation

Name:

```text
bare_command_shows_branded_home
```

Launch `mailghost` with no arguments and `NO_COLOR=1`.

Verify:

- exit status is `0`;
- stderr is empty;
- stdout contains `mailghost`, `Usage`, and `generate`.

Do not assert the complete output or exact spacing.

## Test 2 — Command Catalog and Aliases

Name:

```text
home_lists_commands_and_short_aliases
```

Launch with no arguments and `NO_COLOR=1`.

Verify these semantic pairs independently:

```text
generate / g
messages / m
delete   / d
account  / me
```

Also verify each command description is present. Keep assertions tolerant of
column-width and ASCII-art changes.

## Test 3 — Version and Global Options

Name:

```text
home_shows_version_and_global_options
```

Launch with no arguments and `NO_COLOR=1`.

Verify:

- the current Cargo package version is present;
- `--help` is present;
- `--version` is present.

Use `env!("CARGO_PKG_VERSION")` as the independent expected version rather
than hard-coding `1.0.0`.

## Test 4 — Color Suppression

Name:

```text
no_color_disables_ansi_sequences
```

Launch with no arguments and `NO_COLOR=1`.

Verify stdout does not contain the ANSI control-sequence prefix `\x1b[`.
Do not assert exact color codes.

Captured subprocess output is non-interactive, so it should also be plain
without `NO_COLOR`. Add a separate piped-output test only if this behavior
becomes unclear or regresses.

## Test 5 — Explicit Help

Name:

```text
explicit_help_still_succeeds
```

Launch `mailghost --help`.

Verify:

- exit status is `0`;
- stdout contains the product description and command list;
- stderr is empty.

This protects Clap's normal help path independently of the branded home.

## Test 6 — Version Flag

Name:

```text
version_flag_still_succeeds
```

Launch `mailghost --version`.

Verify:

- exit status is `0`;
- stdout contains `mailghost` and `env!("CARGO_PKG_VERSION")`;
- stderr is empty.

## Test 7 — Invalid Command

Name:

```text
unknown_command_is_rejected
```

Launch `mailghost definitely-not-a-command`.

Verify:

- exit status is non-zero;
- stdout does not contain the branded home;
- stderr identifies the invalid subcommand.

This proves invalid input does not fall through to the zero-argument home.

## Test 8 — Existing Aliases

Name:

```text
short_aliases_reach_their_commands
```

Treat this as a later integration exercise because some commands touch local
state or the Mail.tm provider.

Verify only safe, deterministic alias behavior first. Do not call live Mail.tm
from automated tests. For provider-backed commands, introduce a provider seam
in a separate testing task rather than adding network-dependent tests.

## Completion Gate

Run:

```bash
cargo fmt --all --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --all-targets --locked
```

The suite is complete when:

- every test observes behavior through the compiled binary;
- no test snapshots the full home screen;
- no test depends on exact colors or alignment;
- no automated test accesses Mail.tm;
- changing only the ASCII drawing does not break semantic tests.

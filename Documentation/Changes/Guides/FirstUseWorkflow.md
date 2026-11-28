# First-use workflow guidance

## Behavior

Task `B11-FirstUseGuides` corrects the first-use path for Python integrators and conversion operators.
The guides now check the installed version and reader/writer catalogue before requesting conversion.
They distinguish an illustrative request from qualified input and link unsupported requests to inspection and error recovery.

Repository installation selects a minimal locked environment with `--no-default-groups` and no optional development extra.
Subsequent commands preserve that selection.
The Python package minimum remains 3.11. The repository example selects 3.14 for documented Fusion and research paths.
The worktree procedure fetches and verifies current main before branching.
CLI recovery records operational JSON on standard error and distinguishes invalid usage and interruption.

## Usage

Start with [getting started](../../GettingStarted.md) for an application project.
Use [repository installation](../../Tasks/Install.md) for an isolated checkout.
Read [format selection](../../Tasks/SelectFormat.md) before conversion and [error recovery](../../Tasks/Troubleshoot.md) after refusal.
The [dependency-group gotcha](../../Gotchas/Packaging/DefaultDevelopmentGroups.md) explains the repeated environment selection.

## Verification and limits

Source inspection used main `1619f00bf532caad262d1557bd69281179e5c497`.
The audit compared package metadata, discovery, conversion result forwarding properties, and CLI exception handling.
The guide retains valid lowercase result properties exposed by `ConversionResult`.
The dependency selection follows the [uv sync contract](https://docs.astral.sh/uv/concepts/projects/sync/).
Formatting, link inspection, and rendered review are recorded in the delivery PR.

No installation, command example, conversion, or CAD application execution is claimed by this documentation change.
Representative-user task evaluation remains open under B11.
Rendered review cannot establish screen-reader compatibility or complete standards conformance.
B10 CLI implementation and B01 support evidence remain separate deliveries.

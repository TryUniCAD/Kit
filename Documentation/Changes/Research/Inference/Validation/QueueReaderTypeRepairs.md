# Reader types and queue validation

The merge-group candidate exposed missing type contracts in the count and constraint helpers and CLI receipt checks.
The helpers now declare their inputs and outputs.
Receipt checks read their JSON at the artifact boundary.
The replay case imports its research module from the configured research checkout.

Mirrored scalar binding now uses `BindMirrorField` and `IsAngleMatch` to follow repository naming rules.
Research patch generation uses the renamed module path.
Circle matching explicitly checks the geometry type before reading its radius.

Verification: the complete steering scan passed for 5,050 Python files.
Mypy 2.4.1 with the Linux platform passed for 5,017 source files.
Pyright 1.1.414 reported zero errors across 5,015 source files.
Remote queue acceptance must verify the repaired candidate.
No local tests ran.

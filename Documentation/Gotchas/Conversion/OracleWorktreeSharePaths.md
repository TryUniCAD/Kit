# Isolated oracle share paths

## Expectation

A new isolated Kit worktree is directly accessible to the SOLIDWORKS oracle VM through the existing shared-folder path, and its authoring/debugging scripts can run from that location.

## Actual behavior

The VM sees selected shared folders, not every host checkout path. In this environment its configured `Z:\` mapping reaches the established research root but not a new worktree under the agent's separate application-data directory. The triangle author path returned `TRIANGLE_SCRIPT_ACCESS=unavailable` even though the script existed on the host.

The first debugger-launch failures produced no usable trace events. That lack of evidence must not be mistaken for a malformed native part. Directly opening the same triangle through `OracleLoadDiagnostics.exe` succeeded with one body and the expected geometry.

## Workaround

Use an explicit host research-root argument for the VM: `re/tooling/harness/AuthorTriangles.vbs` requires `/root:"..."` and writes only under a `triangle` child directory. Put controlled research harnesses and newly captured artifacts in the established VM share, copy only those generated research inputs into the isolated checkout for analysis, and never import any vendor stream from production.

Preserve existing experimental files instead of overwriting them. Existing target names are reported as `PREEXISTING_SKIP`. Each controlled or generated native result must still be checked through the real oracle; host-path access alone is not acceptance evidence.

See [the triangle research record](../../re/solidworks/records/PolylineThreePad.md).

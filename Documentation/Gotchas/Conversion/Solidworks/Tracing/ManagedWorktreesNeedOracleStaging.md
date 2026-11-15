# Stage committed oracle scripts for managed worktrees

## Expectation

The Windows guest can read an isolated managed worktree through the Mac home share.

## Observed behavior

The guest could not open `OracleIdentity.py` under the managed `.codex/worktrees/` path in this session.
The same committed script ran from a separate task-owned directory under `Documents/UniCAD/`.
This observation does not establish a restriction for every Parallels share configuration.

## Workaround

Keep repository edits in the isolated worktree.
Stage the committed oracle scripts and remote generated artifacts in a separate guest-accessible research directory.
Verify the script and candidate hashes before inspection.
Keep generator revision, CI artifact identity, and oracle script revision in the measurement record.
Invoke the staged scripts through `prlctl exec` with the current-user option.
Do not stage proprietary vendor software or use the staging directory as writer input.

The [inspection record](../../../../../re/solidworks/measurements/2026/FreshPartProfileOwnership.json) retains the candidate and executable identities.

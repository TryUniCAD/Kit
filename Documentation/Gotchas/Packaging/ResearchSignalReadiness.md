# Research signal fixtures need atomic readiness markers

The signal fixtures wait for the `Ready` path to exist before reading the
selected SDK identity and signalling the launcher. Writing directly to that
path creates an empty file before the text is written, so existence alone can
indicate readiness too early.

Shard 3 failed `CheckSignal[SIGQUIT-True-37]` on merge candidate
`927bed8b4c1b5edfd8041c9849145de630a9294b`. The reader observed an empty
string where it expected `selected research sdk`.
[Merge queue job](https://github.com/TryUniCAD/Kit/actions/runs/44825852618/job/136598583137)

Write and close a temporary sibling, then replace `Ready`. This keeps the
marker in the same directory as its pending contents and makes the complete
identity visible in one filesystem operation.
[Signal ownership](ResearchSignalOwnership.md)

# Document IO validation can import its composing class

## Expectation

Moving document read and file-write guard imports inside IO functions avoids an import cycle.

## Actual behavior

The [queue CodeQL job](https://github.com/TryUniCAD/Kit/actions/runs/45034560056/job/137245293923) reported 19 cyclic-import findings. DocumentIo imported offset policies, which imported DocumentWalk and DocumentBoundary, which imported the document model and its IO behavior. Function-local imports still belong to that dependency graph.

## Workaround

Bind source-read and file-write policies through DocumentValidBehavior's existing validator registry during document composition. DocumentIo imports only the registry boundary and preserves fail-closed policy execution before serialization or file mutation. Do not suppress the CodeQL finding or remove the guards. The [queue repair entry](../../../Changes/Ci/FusionQueueCompatibilityRepair.md) records the associated compatibility repairs and verification limits.

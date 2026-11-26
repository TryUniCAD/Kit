# Restoring an empty sparse worktree can hydrate the full tree

After `git worktree add --no-checkout` and setting sparse paths, `git restore --source=HEAD --staged --worktree :/` filled the temporary evidence worktree with out-of-scope generated files on Windows. The operation ran out of disk while materializing a planner catalogue. The incomplete worktree occupied 867.64 MiB across 11,372 generated files. All those paths came from its pinned Git base. A complete sibling checkout using the same restore command occupied 998.62 MiB until sparse rules were reapplied. The native evidence and user work stayed in their original locations.

Populate the new sparse index with `git read-tree -mu HEAD`. Check the materialized subset with `git ls-files -v`. This initialized only 179 intended paths for the exact-depth evidence task. [Sparse index initialization](../Research/Workers/Verification/SparseWorktreesNeedIndexPopulation.md), [Research worktree storage](ResearchWorktreeDiskUsage.md)

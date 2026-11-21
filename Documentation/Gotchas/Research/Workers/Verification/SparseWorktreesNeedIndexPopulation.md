# Sparse worktrees need index population

A worktree created with `git worktree add --no-checkout` does not have a populated index.
Setting sparse-checkout patterns alone can leave that worktree empty.
The legacy reader fixture then reports a missing checkout instead of exercising decoding compatibility.

The fixture now sets its sparse patterns and runs `git read-tree -mu HEAD` in its owned temporary worktree before launching the reader.
It checks each command's outcome and removes the worktree in the enclosing cleanup path.
Only SDK and automation paths are materialized.

The issue was identified in [PR review](https://github.com/TryUniCAD/Kit/pull/209#discussion_r4649167090).
The Windows and shared process compatibility jobs cover the fixture; no local reproduction was executed.

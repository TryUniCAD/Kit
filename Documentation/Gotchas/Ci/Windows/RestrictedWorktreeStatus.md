# Restricted worktree status can resemble a missing checkout

Expected: Git status can inspect a newly created Windows worktree.

Observed: a restricted session returned `fatal: this operation must be run in a work tree` for a checkout on drive D.
In the same checkout, `git rev-parse --is-inside-work-tree` returned `true` and `core.bare` was `false`.
The status command succeeded when the session granted access to that named checkout.
This observation does not establish a Git configuration defect.

Inspect the resolved checkout and its access permissions.
Request access to that specific checkout when required by the session.
Keep the existing Git configuration and user-owned files intact.
The PR #121 readiness session reproduced both outcomes on 2026-11-28.

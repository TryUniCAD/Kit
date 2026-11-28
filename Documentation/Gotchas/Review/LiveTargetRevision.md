# PR base metadata can retain an older target revision

A successful CI receipt and matching PR `base.sha` can appear to identify the current target branch.
During the PR #398 rollout check, both retained an earlier commit after main had moved; the PR also had conflicts.
The earlier reviewer accepted that metadata pair even though it did not qualify the live target revision.

Read the target Git ref independently during both selection and publication.
Bind the review snapshot to that revision even when the PR has conflicts or unsuccessful CI.
Before approval, require the CI evidence base to match the live target and require GitHub mergeability to be true.
Refresh the branch and applicable CI to qualify approval; analysis does not wait for that qualification.

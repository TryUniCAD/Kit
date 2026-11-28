# PR base metadata can retain an older target revision

A successful CI receipt and matching PR `base.sha` can appear to identify the current target branch.
During the PR #398 rollout check, both retained an earlier commit after main had moved; the PR also had conflicts.
The earlier reviewer accepted that metadata pair even though it did not qualify the live target revision.

Read the target Git ref independently during both selection and publication.
Require its current SHA to equal the CI evidence base and require GitHub mergeability to be true.
Reject conflicts and indeterminate mergeability instead of approving from old metadata.
Refresh the branch and applicable CI before retrying that request.

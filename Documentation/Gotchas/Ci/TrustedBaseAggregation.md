# Trusted-base aggregation

A reporter change on a PR might appear to affect that PR's aggregate. `pull_request_target` loads trusted base code. Merge the reviewed reporter change before relying on its behavior elsewhere. See [the CI allowlist](../../Changes/CiReviewerExclusions.md).

Retire a required workflow in two revisions.
First make its reports optional while continuing to reject reported failures.
After that revision reaches the base, remove the workflow and its obsolete allowlist entry.
Removing both together leaves the current PR waiting for reports required by the trusted base.
The same ordering applies to the merge-group aggregate, which checks out the group's base revision.
See the [compatibility report transition](../../Changes/Ci/CompatibilityReportRetirement.md).

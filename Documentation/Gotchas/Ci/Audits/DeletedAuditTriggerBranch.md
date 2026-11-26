# A deleted audit branch cannot start a new source audit

The historical audit guide points to a push trigger on `codex/rationale-merged-audit`.
That branch no longer existed when a fresh audit of main was requested.
Rerunning an older push keeps its original source SHA, and rerunning PR checks keeps acceptance deferred.
Neither verifies a different current main revision.

Use the manual source-audit trigger with an explicit full commit SHA.
Verify the planner's checkout and the final gate, and report the workflow harness revision separately from the tested source revision.
See [manual source audits](../../../Changes/Ci/Testing/ManualSourceAudit.md).

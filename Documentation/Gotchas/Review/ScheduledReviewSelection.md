# Workflow completion triggers require special trust handling

The security audit rejects privileged `workflow_run` and `issue_comment` triggers even when their handlers validate source input.
The account reviewer instead uses scheduled execution of trusted default-branch code.
It verifies successful aggregate CI evidence before selecting an eligible PR.
Mention discovery also uses trusted scheduled polling, followed by live permission checks in a read-only job.

Selection records the CI run ID on the app's native check.
A successful report needs the actual approving review before selection treats publication as complete.
An unsupported input receives a failed report, so it does not repeatedly prevent other PRs from being selected.

GitHub schedules can be delayed and run only from the default branch.
See [GitHub's schedule reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)
and [the account reviewer procedure](../../Tasks/AccountReviewer.md).

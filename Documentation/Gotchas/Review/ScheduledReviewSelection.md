# Workflow completion triggers require special trust handling

The security audit rejects the privileged `workflow_run` trigger even when its handler validates source input.
The account reviewer instead uses scheduled execution of trusted default-branch code.
It verifies successful aggregate CI evidence before selecting an eligible PR.

Selection records the CI run ID on the app's native check.
A successful report needs the actual approving review before selection treats publication as complete.
An unsupported input receives a failed report, so it does not repeatedly prevent other PRs from being selected.

GitHub schedules can be delayed and run only from the default branch.
See [GitHub's schedule reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)
and [the account reviewer procedure](../../Tasks/AccountReviewer.md).

# Workflow completion triggers require special trust handling

The security audit flags `pull_request_target` and `issue_comment` triggers even when their handlers validate metadata only.
The repository owner explicitly approved two line-scoped `dangerous-triggers` exceptions for the review request dispatcher.
That dispatcher never checks out PR code, reads no app or account secrets and sends only a PR or comment number to the protected default-branch workflow.
Comment requests require live write, maintain or admin permission.
The protected handler repeats admission before accessing private credentials.

Ordinary `pull_request` workflows do not run when a PR has merge conflicts.
The metadata-only target trigger keeps new-commit review dispatch available during conflicts.
Scheduled execution remains recovery and backlog discovery, rather than the only mention trigger.
Selection and analysis are independent of CI success; successful matching CI remains an approval gate.
The native report records the review snapshot, and approval additionally requires the actual approving review.

GitHub schedules can be delayed and run only from the default branch.
See [GitHub's schedule reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)
and [the account reviewer procedure](../../Tasks/AccountReviewer.md).

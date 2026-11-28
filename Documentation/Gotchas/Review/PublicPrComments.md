# Collaborator only PR creation does not restrict PR comments

Restricting PR creation to collaborators might appear to make comment-triggered automation private.
GitHub still permits public comments on visible PRs.
An app mention alone therefore does not establish authorization.

Use the comment author's live repository permissions rather than the PR author's permissions or an association label.
Reject unauthorized commands before accessing app or account credentials.
The account reviewer performs that check in a separate read-only admission job.

See [GitHub's PR access announcement](https://github.blog/changelog/2026-02-04-new-repository-settings-for-configuring-pull-request-access/)
and [the reviewer procedure](../../Tasks/AccountReviewer.md).

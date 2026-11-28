# Queued workflows can restore stale account tokens

Repository secrets appear suitable for a refreshed account login.
However, GitHub reads repository secrets when each workflow queues.
A queued workflow can therefore retain an old token after an earlier workflow rotates it.

Store the login in an environment secret and serialize the account workflow.
GitHub reads environment secrets when their job starts.
Persist the refreshed file before the next account job starts.

See [GitHub's secret timing rules](https://docs.github.com/en/actions/reference/security/secrets)
and [the account reviewer procedure](../../Tasks/AccountReviewer.md).

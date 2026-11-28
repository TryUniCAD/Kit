# Queued workflows can restore stale account tokens

Repository secrets appear suitable for a refreshed account login.
However, GitHub reads repository secrets when each workflow queues.
A queued workflow can therefore retain an old token after an earlier workflow rotates it.

Store the login in an environment secret and serialize the account execution job through credential persistence and native publication.
GitHub reads environment secrets when their job starts.
Persist the refreshed file before the next account job starts.
Admission, source collection and message acknowledgement can run concurrently without reading or refreshing that login.
Recheck native receipts after acquiring the account lock to avoid duplicate automatic reviews prepared while another job was still running.

See [GitHub's secret timing rules](https://docs.github.com/en/actions/reference/security/secrets)
and [the account reviewer procedure](../../Tasks/AccountReviewer.md).

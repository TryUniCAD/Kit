# Account authenticated GitHub App review

The account reviewer prepares bounded source input after successful PR aggregate CI.
It runs Codex in an isolated container on a GitHub-hosted runner.
It validates the model's structured result before the app publishes findings and a five-point soundness score.
Only complete, clean reviews with matching scope and a score of at least four can approve.

The model receives no GitHub publishing credential and executes no proposed repository code.
Separate app tokens persist the rotated environment secret and publish the native review.
Review never enrolls a PR in the merge queue or bypasses acceptance.

See [setup and limitations](../Tasks/AccountReviewer.md).
Activation requires an installed app, verified reviewer identities, and a dedicated account login.
The verified app identity replaces the former reviewer in the registry.
Review instructions now follow its automatic workflow instead of posting a comment trigger.
App ownership, bot identity, corrected permissions, protected environment policy, and secret names were verified through GitHub.
A short-lived read-only installation token confirmed access to Kit and was revoked.
The planning builder and its freshness check passed with the locked environment using `--no-sync`.
Python formatting and whitespace checks passed.
No live account-authenticated review, credential rotation, or native approval has passed yet.
Source inspection is not end-to-end acceptance.

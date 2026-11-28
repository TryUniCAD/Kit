# Configure account authenticated review

## Purpose

Run automated reviews on GitHub-hosted runners without an always-on server.
The GitHub App posts findings, a five-point soundness score, a native check, and a revision-bound review.
The workflow never merges a PR or enrolls it in the merge queue.
The scheduled workflow checks for eligible successful PR CI runs every five minutes.
GitHub can delay scheduled execution; this is not an immediate completion hook.
Trusted collaborators can also request review with mention commands polled by that same scheduled workflow.

## Before you start

You need organization owner access, a dedicated Codex login, and a GitHub App installed on Kit.
Keep public PR creation restricted to collaborators.
OpenAI advises against account-authenticated automation for public repositories, including this repository.
The repository owner explicitly selected this authentication method despite that warning.
Isolation reduces exposure but does not establish a risk-free setup.

Read [the account authentication guidance](https://learn.chatgpt.com/docs/auth/ci-cd-auth).
Do not reuse the CI session on another machine after seeding it.
Do not place account credentials in chat, source control, artifacts, or logs.

## Register the app

1. Open [TryUniCAD app registration](https://github.com/organizations/TryUniCAD/settings/apps/new).
2. Choose a unique app name and use the Kit repository URL as its homepage.
3. Disable webhooks and user authorization during installation.
4. Limit app installation to the owning organization.
5. Set these repository permissions.

| Permission    | Access | Purpose                                                 |
| ------------- | ------ | ------------------------------------------------------- |
| Pull requests | Write  | Publish approving or change-requesting reviews          |
| Checks        | Write  | Publish the app's own review report                     |
| Actions       | Read   | Verify successful aggregate CI evidence                 |
| Contents      | Read   | Read repository identity and metadata                   |
| Environments  | Write  | Persist the refreshed CI login as an environment secret |
| Issues        | Write  | React to an admitted PR comment as the installed app    |

6. Register the app and install it on Kit only.
7. Generate a private key and store it outside repository checkouts.
8. Set repository variable `REVIEW_APP_ID` to the numeric app ID.
9. Store the key in environment secret `REVIEW_APP_PRIVATE_KEY` under `AccountReview`.

The Actions approval checkbox controls `GITHUB_TOKEN` and is not required for this app.
The app tokens are restricted separately for credential persistence and review publication.
The model container receives neither token nor the app private key.

## Seed account authentication

1. Create a dedicated temporary Codex home outside the checkout.
2. Sign in with file-backed credential storage.

```sh
CODEX_HOME=/private/tmp/KitReviewLogin codex -c 'cli_auth_credentials_store="file"' login
```

3. Create the `AccountReview` repository environment.
4. Restrict environment deployments to the protected default branch.
5. Store that login's `auth.json` as environment secret `CODEX_AUTH_JSON`.
6. Do not configure manual environment approval if unattended reviews are required.

Use a private secret channel or GitHub's secret interface for credential transfer.
The runner writes rotated credentials back after the model process exits.
Environment secrets load when their job starts, so serialized runs receive the latest token bundle.
The trusted workflow queues up to 100 requests and never intentionally cancels an active credential refresh.

## Activate and verify

1. Resolve the app's actual app ID, bot account ID, and login from GitHub.
2. Replace the previous reviewer in `ReviewBot.json` with those verified identities and the app's native check name.
3. Update the skill's trigger instructions to use automatic review after aggregate CI.
4. Set repository variable `ACCOUNT_REVIEW_ENABLED` to `true` only after the configuration is accepted.
5. Open a bounded same-repository PR authored by a collaborator with write access.
6. Wait for `Pull Request / CI Agg` and its immutable evidence artifact.
7. Verify the app's review identity, reviewed head and base, findings, score, and native report.

Manual reruns use the `Account review` workflow with the successful PR CI run ID as input `id`.
For a mention request, post one complete command from `AccountReview.MentionCommands` in the reviewer registry as a new PR comment.
The commenter must have current write, maintain, or admin permission on the repository.
Mention requests inspect the commented PR and allow an explicit reassessment of its current head.
They search the 100 most recent successful PR CI runs.
If current successful CI is unavailable, no model job starts; scheduled review can follow after CI succeeds.
Mentions inside quotes, longer comments, edited comments, bot comments, and ordinary issue comments are ignored.
Public comment admission runs without app or account credentials.
After complete input is prepared, the app adds an eyes reaction to an admitted mention.
When publication finishes, that reaction is replaced with thumbs up for a verified approval or thumbs down for verified requested changes.
Runtime or publication failure receives a confused reaction instead.
Reactions describe request progress; only the native report and review establish the result.
If GitHub cancels the entire workflow or reaction publication fails, the progress reaction can remain until a successful retry.
The starting and completion reaction steps use separate app tokens that never enter the model container.
Polling inspects the latest 100 repository comments and rotates through at most ten matching commands per invocation.
The workflow run number advances the start position so completed requests do not permanently block older requests in that window.
The app's native report marks a handled mention for the inspected head, preventing repeated requests from one unchanged comment.
A neutral waiting-for-CI report does not establish a completed review or approval.
Receipt discovery includes all retained matching app checks with pagination.
Each scheduled invocation selects one unreported eligible run from the 30 most recent successful PR CI runs.
Closed, draft, forked, obsolete, and previously reported inputs are skipped.
Use manual dispatch for an older run outside that window or an explicit reassessment.
Unsupported input receives a failed native report and no approval, so it cannot block discovery of later candidates.
The trusted workflow and scripts must exist on the default branch before automatic execution.
Registration, installation, configuration, and activation are separate from implementation publication.

## Approval policy

Approval requires a complete review, matching scope, a score of at least four, and zero unresolved findings at every priority.
The score alone never authorizes approval.
Malformed output, missing evidence, fork PRs, drafts, changed revisions, and untrusted authors stop publication.
CI evidence must match the live target branch ref, and GitHub must report the PR as mergeable.
An old `base.sha` in PR metadata does not establish the current target branch revision.
Changed binaries and sources over 160,000 bytes require a separate review.
The input limit is 40 changed files and 900,000 encoded bytes.
These limits refuse reviews instead of silently truncating them.
The model must report incomplete review when surrounding context is insufficient.

Review is separate from native CAD acceptance, CI health, and merge authorization.
Existing merge-queue acceptance remains mandatory.
No model score guarantees that a change cannot introduce a defect.

## Review runtime

`AccountReview.Model` and `AccountReview.ReasoningEffort` in the reviewer registry define the default runtime for every review trigger.
The runner passes both values explicitly to Codex instead of using the CLI default.
The requested default is `gpt-6.1-terra` with `medium` reasoning.
Unsupported model or reasoning settings fail the job without selecting another model.
The published review records the selected model and reasoning alongside its revision evidence.

## If the task fails

If token refresh fails, reseed the environment secret using a new dedicated login.
If persistence fails, stop subsequent runs and reseed before retrying.
If CI evidence expired or the PR changed, rerun applicable CI before review.
If the app identity is absent from the registry, complete verified configuration before activation.
Do not restore the previous reviewer as an automatic fallback.

## Current evidence

Implementation is under scope `AccountReviewer` in the [planning register](../Planning/Links.json).
App registration, bot identity verification, and reviewer replacement are recorded in this implementation.
The owner updated the app display name and organization logo.
The public app, installed app, bot account, and downloaded public avatar were verified after that change.
The configuration command refreshes mention commands from the verified app slug when an app is renamed.
Corrected permissions, protected environment secret storage, and a temporary read-only Kit installation token were verified during setup.
That token was revoked after verification.
At the owner's explicit request, initial seeding uses the existing local account session.
Local and CI refreshes can conflict; reseed CI if either copy can no longer refresh.
Hosted execution, live credential rotation, and review acceptance remain pending.
Project synchronization is pending because this session's token lacks project scopes.

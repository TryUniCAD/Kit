# Configure account authenticated review

## Purpose

Run automated reviews on GitHub-hosted runners without an always-on server.
The GitHub App posts findings, a five-point soundness score, a native check, and a revision-bound review.
The workflow never merges a PR or enrolls it in the merge queue.
A metadata-only dispatcher requests review when a PR opens, changes, or receives an authorized mention.
The owner approved only its two line-scoped Zizmor trigger exceptions; it never checks out PR code or reads private credentials.
Review runs even when CI fails, the PR is a draft, or its branches conflict.
A five-minute scheduled scan provides recovery and backlog discovery; GitHub can delay schedules.
Approval remains a separate, stricter decision.

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
Environment secrets load when their job starts, so serialized account jobs receive the latest token bundle.
The account job queues up to 100 requests and never intentionally cancels an active credential refresh.
It retains the lock through native publication and rechecks existing reports after acquisition.
Admission, source collection and progress reactions can run while another account job is active.

## Activate and verify

1. Resolve the app's actual app ID, bot account ID, and login from GitHub.
2. Replace the previous reviewer in `ReviewBot.json` with those verified identities and the app's native check name.
3. Update the skill's trigger instructions to review each proposed head independently of CI.
4. Set repository variable `ACCOUNT_REVIEW_ENABLED` to `true` only after the configuration is accepted.
5. Open a same-repository PR or submit an authorized mention.
6. Verify dispatch starts without waiting for CI; successful current CI is required only for approval.
7. Verify the app's review identity, reviewed head and base, findings, score, and native report.

Manual reruns use input `pull` with a PR number and optional `force=true`.
Input `comment` processes a specific authorized conversation comment through the same admission boundary.
The legacy `id` input still selects the PR from a successful CI receipt but is not required for review.
For a mention request, post one complete command from `AccountReview.MentionCommands` in the reviewer registry as a new PR comment.
The commenter must have current write, maintain, or admin permission on the repository.
Mention requests inspect the commented PR and allow an explicit reassessment of its current head.
They snapshot the live proposed head and target branch directly.
Failing or missing CI and merge conflicts do not prevent model review.
Mentions inside quotes, longer comments, edited comments, bot comments, and ordinary issue comments are ignored.
Public comment admission runs without app or account credentials.
The app adds an eyes reaction after authorization and before source collection begins.
When publication finishes, eyes is replaced with thumbs up for verified approval, thumbs down for requested changes, or hooray for a completed comment-only review awaiting approval conditions.
Runtime or publication failure receives a confused reaction instead.
Each transition removes the bot's older lifecycle reactions, so a retry does not retain an obsolete failure or approval indicator.
Failure also publishes a failed native report with its workflow log link, so automatic reviews without a mention remain observable.
Reactions describe request progress; only the native report and review establish the result.
If GitHub cancels the entire workflow or the completion job fails, the progress reaction can remain until a successful retry.
The starting and completion reaction steps use separate app tokens that never enter the model container.
Both tokens need Issues write and Pull requests write for this repository's PR conversation reactions.
Polling inspects the latest 100 repository comments and rotates through at most ten matching commands per invocation.
The workflow run number advances the start position so completed requests do not permanently block older requests in that window.
The app's native report marks a handled mention for the inspected head, preventing repeated requests from one unchanged comment.
A completed code review can have a neutral report and native comment while approval conditions remain unmet.
That comment and its score do not substitute for approval.
Receipt discovery includes all retained matching app checks with pagination.
Scheduled recovery rotates through twenty open PRs per invocation and selects one unreported snapshot.
A snapshot binds the current head, live target, title, description, trusted policy revision, and runtime.
A new commit changes that identity and requires a new review.
Closed, forked, obsolete, and previously reported snapshots are skipped.
Background discovery requires a trusted author; an authorized collaborator request can admit any same-repository PR.
A neutral clean review is reconsidered when approval conditions become ready.
Runtime failures are recorded and need a new request or revision before retry.
The trusted workflow and scripts must exist on the default branch before automatic execution.
Registration, installation, configuration, and activation are separate from implementation publication.

## Approval policy

Approval requires complete source coverage, a complete scope-matching review, a score of at least four, and zero unresolved findings at every priority.
It also requires a non-draft mergeable PR, completed successful CI, and an immutable trusted CI receipt matching the current head and live target.
The score alone never authorizes approval.
Reviews use a [verdict-first presentation](../Changes/Review/ReviewPresentation.md) with priority-grouped findings and collapsible verification details; presentation never changes the approval decision.
Malformed output, fork PRs, changed revisions, and unauthorized requests stop publication.
CI failure, drafts, or conflicts permit review publication but forbid approval.
CI evidence must match the live target branch ref, and GitHub must report the PR as mergeable.
An old `base.sha` in PR metadata does not establish the current target branch revision.
Model input is bounded to forty files and 900,000 encoded bytes; individual sources are bounded to 160,000 bytes.
Code is prioritized before generated views. Binary, oversized, and omitted sources are explicitly identified as unavailable.
The two generated planning BoardData outputs can instead carry exact reconstruction receipts under the [strict generated coverage requirements](../Changes/Review/GeneratedPlanningCoverage.md).
This requires an unchanged trusted generator, unchanged other dependencies, fully supplied supported input changes, matching before and after bytes, and a current trusted base.
Failed or unsupported reconstruction retains partial coverage and never authorizes approval.
The available source can still receive a partial review, but the trusted publisher refuses approval whenever source coverage is incomplete.
The model must report incomplete review when surrounding context is insufficient.
Before-content comes from the merge base; target-content shows concurrent changes on the live target.
Project policy comes from the trusted workflow revision, so older stacked branches do not need to contain newer policy files.
`AccountReview.RequestProtocol` coordinates dispatcher rollout with the trusted handler.

Review is separate from native CAD acceptance, CI health, and merge authorization.
Existing merge-queue acceptance remains mandatory.
No model score guarantees that a change cannot introduce a defect.

## Review runtime

`AccountReview.Model` and `AccountReview.ReasoningEffort` in the reviewer registry define the default runtime for every review trigger.
The runner passes both values explicitly to Codex instead of using the CLI default.
The requested default is `gpt-6.1-terra` with `medium` reasoning.
Unsupported model or reasoning settings fail the job without selecting another model.
The published review records the selected model and reasoning alongside its revision evidence.
The pinned image exports its Node binary's public certificate authorities to a PEM file and supplies it through `CODEX_CA_CERTIFICATE` and `SSL_CERT_FILE`.
This restores native-client TLS trust without disabling certificate verification or downloading another authority bundle.

## If the task fails

If token refresh fails, reseed the environment secret using a new dedicated login.
If persistence fails, stop subsequent runs and reseed before retrying.
If the PR changed, request review for the new snapshot.
If CI evidence expired or is stale, refresh CI before approval; review can still run.
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

## Recover redundant patch capacity

The source collector keeps patches when the context fits. Before rejecting source snapshots for the 900,000-byte encoded budget, it removes duplicate patches for entries whose complete before and after text is retained. Proposed and live-target source text is unchanged. Partial or unavailable source keeps its omission status, and a context that still cannot fit remains incomplete or fails the final byte guard.

This does not increase the forty-file or 160,000-byte limits. It does not qualify binary input, change generated-source verification or replace an actual approving review. [Change and verification](../Changes/Review/CompleteSourceBudget.md) · [Duplicate patch gotcha](../Gotchas/Review/RedundantPatchCapacity.md)

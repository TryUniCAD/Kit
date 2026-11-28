# Configure account authenticated review

## Purpose

Run automated reviews on GitHub-hosted runners without an always-on server.
The GitHub App posts findings, a five-point soundness score, a native check, and a revision-bound review.
The workflow never merges a PR or enrolls it in the merge queue.

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
The workflow queues up to 100 runs and never intentionally cancels an active credential refresh.

## Activate and verify

1. Resolve the app's actual app ID, bot account ID, and login from GitHub.
2. Replace the previous reviewer in `ReviewBot.json` with those verified identities and the app's native check name.
3. Update the skill's trigger instructions to use automatic review after aggregate CI.
4. Set repository variable `ACCOUNT_REVIEW_ENABLED` to `true` only after the configuration is accepted.
5. Open a bounded same-repository PR authored by a collaborator with write access.
6. Wait for `Pull Request / CI Agg` and its immutable evidence artifact.
7. Verify the app's review identity, reviewed head and base, findings, score, and native report.

Manual reruns use the `Account review` workflow with the successful PR CI run ID as input `id`.
The trusted workflow and scripts must exist on the default branch before automatic execution.
Registration, installation, configuration, and activation are separate from implementation publication.

## Approval policy

Approval requires a complete review, matching scope, a score of at least four, and zero unresolved findings at every priority.
The score alone never authorizes approval.
Malformed output, missing evidence, fork PRs, drafts, changed revisions, and untrusted authors stop publication.
Changed binaries and sources over 160,000 bytes require a separate review.
The input limit is 40 changed files and 900,000 encoded bytes.
These limits refuse reviews instead of silently truncating them.
The model must report incomplete review when surrounding context is insufficient.

Review is separate from native CAD acceptance, CI health, and merge authorization.
Existing merge-queue acceptance remains mandatory.
No model score guarantees that a change cannot introduce a defect.

## If the task fails

If token refresh fails, reseed the environment secret using a new dedicated login.
If persistence fails, stop subsequent runs and reseed before retrying.
If CI evidence expired or the PR changed, rerun applicable CI before review.
If the app identity is absent from the registry, complete verified configuration before activation.
Do not restore the previous reviewer as an automatic fallback.

## Current evidence

Implementation is under scope `AccountReviewer` in the [planning register](../Planning/Links.json).
App registration, bot identity verification, and reviewer replacement are recorded in this implementation.
Corrected permissions, protected environment secret storage, and a temporary read-only Kit installation token were verified during setup.
That token was revoked after verification.
At the owner's explicit request, initial seeding uses the existing local account session.
Local and CI refreshes can conflict; reseed CI if either copy can no longer refresh.
Hosted execution, live credential rotation, and review acceptance remain pending.
Project synchronization is pending because this session's token lacks project scopes.

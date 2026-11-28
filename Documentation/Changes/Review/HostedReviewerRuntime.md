# Restore hosted review connections and reactions

The deployed account reviewer could not start a model review or acknowledge PR mentions.
PR #402 installed its dispatcher, but live acceptance exposed two runtime failures.

The pinned slim Linux image has no system CA bundle.
The image now exports the public certificate authorities already bundled in its pinned Node binary and points `CODEX_CA_CERTIFICATE` and `SSL_CERT_FILE` at that PEM file.
Certificate verification remains enabled.
No new certificate download, package version or account credential is introduced.

Both starting and completion reaction tokens now request Issues write and Pull requests write.
The app installation already has those permissions.
Tokens remain restricted to this repository and trusted host steps; they never enter the model container.

New mention requests and other PRs can pass admission, prepare input and publish progress reactions while an account job is active.
Repeat dispatches for the same request remain serialized.
Only the account execution, credential persistence and native publication job holds the existing serialization lock.
It rechecks the live snapshot and existing native receipt after acquiring that lock, so queued duplicate automatic requests reuse the actual report.
Explicit mentions and forced reassessments still run.
Publication remains outside the isolated model container, and the refreshed login is persisted before the next account job starts.
Each lifecycle transition replaces the bot's older managed reactions, including a prior failure reaction after a retry.

The complete suite gains a process smoke that executes the production certificate exporter and establishes verified TLS to the account-service hostname.
It runs through the existing merge-queue planner, shards and report.
An HTTP response proves TLS connectivity only; it does not prove authentication or a completed model review.

## Verification

- [Automatic run 46171114534](https://github.com/TryUniCAD/Kit/actions/runs/46171114534) reached mention acknowledgement and failed before source preparation.
- Real installation-token probes on the PR #398 conversation returned HTTP 403 for Issues write alone and for Issues write plus Pull requests read. Both write scopes returned HTTP 201 and the registered bot identity. Every probe token was revoked.
- [Fixture run 46171251547](https://github.com/TryUniCAD/Kit/actions/runs/46171251547) built the container, then reported `account service connection failed` from the model process.
- All five layers of the exact pinned Linux image were streamed with their SHA-256 digests verified. The final filesystem has no `/etc/ssl/certs/ca-certificates.crt`. The selected Linux manifest is `sha256:d20a7b8b4184bf74fe77499b5460a3d69e582bc733d50287e40c3fe791764851`.
- The production exporter produced 146 usable authorities locally and reached `https://chatgpt.com/` with verified TLS. Its public HTTP 403 response establishes TLS only.
- A [real fixture mention](https://github.com/TryUniCAD/Kit/pull/401#issuecomment-7243325861) automatically started [dispatcher run 46172610068](https://github.com/TryUniCAD/Kit/actions/runs/46172610068), which passed. Worker reactions and model acceptance remain separate pending checks.
- The real queued-receipt process reused the fixture's existing native report with `run=false` and retained explicit forced reassessment with `run=true`, using actual hosted input and live GitHub checks without account credentials or mocked APIs.

Hosted model output, automatic message reactions, native findings and clean-head app approval still require verification after deployment.
The review model, reasoning setting, source coverage limits, approval requirements and merge-queue gates remain unchanged.

See [the operating procedure](../../Tasks/AccountReviewer.md),
[certificate-store evidence](../../Gotchas/Review/RuntimeCertificateStore.md)
and [reaction permission evidence](../../Gotchas/Review/ReactionPermissions.md).

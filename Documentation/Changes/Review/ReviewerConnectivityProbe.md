# Reviewer connectivity probe

The `Account review` workflow accepts `connectivity_probe=true` on manual dispatch.
Run it on a reviewed ref that contains the probe.
The probe builds the trusted reviewer image at `68cec987d0b720762ae95f2f92799eb113d23b44` on `ubuntu-24.04`.
It reports the DNS, TLS, and credential-free HTTP HEAD result for two fixed service hosts.
Each phase has a time limit, and a failed request exits unsuccessfully.
The workflow probe does not enter the protected review environment or pass account credentials to the container.
It has its own concurrency group and leaves the normal review path unchanged when disabled.

HTTP status shows that the Node request reached an HTTP service.
This diagnostic does not verify the Rust Codex client's transport, account authentication, model access, or review approval.
The [review guide](../../Tasks/AccountReviewer.md#probe-hosted-connectivity) gives the dispatch procedure.

Local verification covered patch applicability, the YAML job dependency structure, Bash and Node syntax, and pinned formatting.
The local Windows Node 24.14.0 process reported successful DNS and TLS checks, followed by HTTP 405 for both hosts.
This local result does not establish hosted-container reachability. The [hosted run](https://github.com/TryUniCAD/Kit/actions/runs/46177424027) passed on probe revision `b940314f169c7e97f42c0723033dbd2ea6fea269`.
Its pinned container also reported DNS and TLS success, followed by HTTP 405 for both hosts.
All five credentialed review-path jobs were skipped.
The [receipt](../../../re/automation/ReviewConnectivity/HostedReceipt.json) retains the exact run, job and source identities.
The authenticated review failure remains unresolved; this probe establishes no review approval.

See [transport evidence limits](../../Gotchas/Ci/Review/ReviewTransportEvidence.md).

Main `141f396f183220e691194907cdcacb7ba56d9ce6` subsequently added a public certificate store for the native client.
The readiness merge keeps its per-request dispatch and serialized credentialed account job.
The diagnostic keeps its separate group and the original pinned runtime so the retained receipt remains reproducible.
No additional hosted diagnostic or authenticated model success is claimed by this merge.

# A supervised worker has a private home directory

## Expectation

An installed personal CAD client can locate its private configuration when a research worker imports it.

## Observed behavior

The supervisor gives each worker an isolated home directory.
The personal client's default `Path.home()` resolves inside that worker's session, not the owner's configuration directory.
Eleven initial unequal-axis verification jobs failed before native submission because their configuration file was absent there.
No native request was retried or session recovered for those preparation failures.

## Workaround

Bind the existing client's configuration base explicitly to the selected private client directory.
Keep the credential file outside the repository and worker artifacts.
Preserve the supervisor's isolated home and the original failed receipts.
Use distinct follow-up job identities after correcting the transport configuration.

The [campaign package](../../../../../re/Fusion/UnequalAxis20261127/README.md) retains the corrected worker and failure evidence.

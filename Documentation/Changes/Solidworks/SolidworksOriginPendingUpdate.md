# SOLIDWORKS origin pending update

The origin factory now retains its native constructor update flag until the first solve
Previously, it cleared the flag while keeping unsolved sketch and point states
That combined states from different lifecycle phases

No caller argument changes are required
Pass a fresh allocated model-feature node to `origin_profile` as before
The factory retains its serialized `f0c` bit zero and the native constructor values for sketch status, entity status and colour
It does not substitute values from a saved origin

The native per-feature admission helper first tests the feature's own needs-update result
A dirty part alone does not guarantee origin admission
The [construction ledger](../../../re/solidworks/records/ProfileConstruction2026.md#pending-origin-admission) records the actual prepass, runtime admission flag and engine dispatch chain
The [pending-origin gotcha](../../Gotchas/Conversion/Solidworks/Profile/PendingOriginNeedsNativeFlag.md) explains the premature clear

The process regression now serializes a complete origin profile through an object archive and container
It checks the decoded update flag, constructor statuses, origin marker, logical constraint and actual profile-owner identity
It also requires identical re-encoding under the runtime file-read guard
Static syntax and diff checks are the local verification boundary
The process regression executes only in remote CI
No local tests, builder imports, reproductions or oracle calls were run

The native admission rule does not establish successful target loading, solving, body generation or held-out acceptance

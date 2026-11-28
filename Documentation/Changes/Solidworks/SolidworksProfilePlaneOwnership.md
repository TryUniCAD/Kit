# SOLIDWORKS profile plane ownership

The fresh profile factory now rejects reuse of a component-plane wrapper by another independent profile
Previously, the origin and polygon could adopt the same wrapper object
Native profile-data destruction directly deletes that allocation, so independent owners require separate wrappers

Supply a separate `component_plane` result to each `origin_profile` or `closed_profile` call
The wrappers can reference the same principal plane and model through their normal object relationships
Each wrapper also requires its own component copy, as the [component ownership finding](../../Gotchas/Conversion/Solidworks/Model/PlaneReferencesOwnTheirComponents.md) records

The [profile construction ledger](../../../re/solidworks/records/ProfileConstruction2026.md#profile-plane-ownership) binds the adoption, replacement and destructor proof to the 2026 binary
The factory records the owning profile as semantic metadata and rejects conflicting ownership before constructing another sketch
That metadata is not a serialized native field
The ledger also distinguishes origin repair admission, ordinary engine dispatch and the remaining native solve-scheduling question

The focused process check now attempts conflicting adoption, constructs an origin with a separate wrapper, and checks the owner identities
The process also retains the binary origin archive round trip and runtime file-read guard
Local verification is limited to static syntax and diff checks
The process regression executes only in remote CI
No local tests, builder imports or oracle calls were run
The [shared API budget finding](../../Gotchas/Ci/Audits/GithubInstallationBudget.md) records an infrastructure failure during remote verification

This repair does not establish generated-file acceptance, origin solver results or native rebuild correctness

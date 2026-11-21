# SOLIDWORKS origin point marker

The fresh origin builder now sets packed point flag bit zero from the native origin initializer
Previously it set point type one but retained the ordinary point marker
The native loader reconstructed runtime origin flag zero from that combination, so the native `isOrigin` predicate returned false
The point type and origin marker are separate fields

The rule comes from the 2026 initializer, serializer, loader and getter
It does not copy saved status two or colour four from a template-loaded origin
Use `origin_profile` as before; ordinary polygon points retain a clear origin marker
See [the construction ledger](../../../re/solidworks/records/ProfileConstruction2026.md#origin-profile-construction) for the exact native addresses
The [origin-flag gotcha](../../Gotchas/Conversion/Solidworks/Profile/OriginPointFlag.md) explains the overlapping decompiler local that concealed the mutation

A focused process regression now constructs an origin under the runtime-read guard, writes its sketch through a binary object archive and container, decodes it, checks the marker and logical constraint, and verifies unchanged re-encoding
It also checks that ordinary polygon vertices remain unmarked
Local verification is limited to static syntax and diff checks; the process regression runs only in remote CI
No local tests, builder imports or oracle calls were run
The complete generated document, first origin solve and later rebuild remain unaccepted

# Principal-plane handles store creation times

## Expectation

The sketch support can be read using the version prefix, fixed timestamp and principal-plane IDs from one older vendor save.

## Observed behavior

SOLIDWORKS 2026 serializes `19000` before the actual model's persistent plane ID and its creation-log time. An ordinary generated part uses principal plane IDs 14 through 16 and a no-log time of `2592000`. A disclosed native Top and Right pair uses IDs 3 and 4 and time `1794529625`. The legacy exact check missed both pairs. With canonical XML role labels, the stream-order fallback still put Top and Right sketches on Front. [Disclosed archive evidence](../../../../../re/solidworks/records/PrincipalPlaneHandles2026.md).

## Workaround

Use a complete handle within the owning sketch's native record and resolve its plane ID against that model's decoded planes. The proven origin-centered principal records carry a zero optional reference, a matching axis kind and the actual sketch basis. Parse the creation-time field at its documented width. Preserve the established path for earlier records and reject ambiguity within the current one.

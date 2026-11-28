# Boundary edge IDs are not downstream edge IDs

A previous/next edge's earlier downstream allocation might appear to explain why a start/end face role is absent. The pinned 2026 source instead queries `EDGE_PERM_ID_2001`. `EDGE_ID_2001` is a separate sketch/entity pointer attribute; `DOWNSTREAM_EDGE_ID` is another separate definition.

The native constructor builds the reference before appending its downstream row and attaching that row's downstream attribute. Those attachments do not change the permanent-ID predicate. A successful permanent lookup supplies an actual edge representation and suppresses that face-role insertion; an unsuccessful lookup uses the previous/next fin's actual right face and its allocated face ID.

Track these three definitions separately. Follow real loop previous/next links and retain equal face IDs under distinct role keys. Do not use edge-array order, mere downstream attribute presence or a captured per-edge table. The [source record](../../../../../../re/solidworks/records/DownstreamBoundaryRoles2026.md) and [receipt](../../../../../../re/solidworks/measurements/2026/DownstreamBoundaryRoleSource01.json) bind the exact modules and addresses. The recipe covers role assignment only; later ambiguity/cache state and nonordinary branches still need their own proof.

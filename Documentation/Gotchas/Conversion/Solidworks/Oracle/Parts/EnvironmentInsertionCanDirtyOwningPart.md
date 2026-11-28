# Environment insertion can dirty its owning part

A clean serialized part status does not imply that ordinary post-load feature insertion preserves it. The pinned 2026 environment insertion requests state 11 on its actual folder when dirty propagation is enabled, and the folder propagates to the part. A later request to clear the added ambient child targets a no-mutation leaf and does not clear its owning part.

Use the actual inserted member, owner and reload gate when reproducing the transition. The reload check accepts any real light. The application supplies the default attributes from session settings. [Exact source and native observation](../../../../../../re/solidworks/records/PartEnvironmentDirtyPropagation2026.md)

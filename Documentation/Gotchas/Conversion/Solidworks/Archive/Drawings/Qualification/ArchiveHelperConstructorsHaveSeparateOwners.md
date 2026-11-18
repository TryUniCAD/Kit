# Archive helper constructors have separate owners

An imported class name does not establish which constructor initializes an archive context. The lower `sldmfcu` constructor takes an archive, owner, conditions, model context, and history. The ordinary `SolidStorage_c::LoadDefinition` path instead uses a separate exported `slduiu` constructor taking the archive and model context.

Tracing only direct calls to the lower constructor misses the real Definition owner. In this build `doccplu` also reaches it through an import jump thunk, so a census limited to direct IAT calls misses that caller.

Bind the actual imported overload, thunk, export, and complete native body before using constructor state. Both overloads clear helper+48, but cold initialization alone does not prove arbitrary callback preservation. A nonzero helper+48 selects a different legacy entity-ID encoding and must keep a closed unsupported boundary until that path is independently implemented.

[Exact original-build addresses, hashes, and scope](../../../../../../../re/solidworks/records/DrawingEdgeReferenceArchive2026.md). No vendor bytes or listings are included.

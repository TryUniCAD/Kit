# Surface bodies set a flag after archive load

The separate `moCompSurfaceBody_c` serializer delegates to the same `moCompAtomBody_c` body as `moCompSolidBody_c`. After delegation it calls `su_CArchive::IsLoading` and sets bit `0x4` at runtime offset `+0x68` on the load path. Treat the operation as a load fixup. Adding a surface-only flag word would advance the archive cursor and misalign the next object. Keep the actual solid or surface class tag, and model the common body once. [Pinned component bodies](../../../../../../re/solidworks/records/DownstreamStandaloneBodyCodec2026.md)

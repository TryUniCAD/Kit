# Preserve fixed components in complete typed assembly reads

Normal `open_document` reads now preserve the fixed occurrence flag for fully
admitted ordinary planar-mate assemblies. The reader projects the actual linked
`moReference_c.f408` Boolean onto the matching neutral component instance,
independently of solver status. Previously every public instance used the
legacy `fixed=False` default.

The projection requires the complete direct occurrence set, actual names,
persistent IDs and serialized backlinks. Deferred and unsupported typed graphs
retain their existing behavior. No public writer or part-preparation route is
enabled by this change.

The [original and native-saved process receipt](../../../../../re/solidworks/measurements/2026/SdkOrderedAssemblyPublicReadback01.json)
checks two normal SDK reads with zero COM imports. Both preserve flags
`[true, false]`, three ordered mates, six actual child plane links, both
configuration names, child D1 and independent rotated placements; the distance
reads back as 47.35 and 63.21 mm respectively. The permanent generated-pair
process integration also passes both authored anchor choices and deferred-read
rejection. Scoped formatting, lint, typing and steering checks pass.

[Construction and evidence](../../../../../re/solidworks/records/SdkPublicAssemblyAnchors2026.md)
· [Native lifecycle](../../../../../re/solidworks/measurements/2026/SdkOrderedAssemblyNative01.json)
· [Anchor-state gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Assembly/PublicAnchorsNeedTypedState.md)

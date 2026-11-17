# Populated mate groups load their children from a separate stream

The resolved-feature copy of a mate group can have an empty child list
even when the application displays mates beneath that group. In the
three disclosed 2026 planar assemblies, the complete mate object is in
`Config-0-MatesList` and its occurrence chains refer to preceding map
entries. Reading the mate list with a fresh object map loses those bindings.

Carry the resolved-feature map into the mate-list codec and check
`MatesList` before interpreting an empty resolved group as an unmated
assembly. The native save prefix is the final map count.
[Typed stream comparison](../../../../../../re/solidworks/records/AssemblyMatesList2026.md#populated-planar-mates)

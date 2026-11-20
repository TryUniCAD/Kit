# SOLIDWORKS assembly component history archives

The version-19000 assembly resolved stream admits the measured
`moHistoryCompItemData_c` schema-one owner and its concrete chain, reference
and external-feature list classes. The actual history pointer uses the shared
map. The reader holds the native history context while it resolves that
pointer and restores it on exit.

Two disclosed assembly controls reproduce Config-0, ResolvedFeatures and
MatesList byte for byte. The two-component case retains its three actual
mate roots. This qualification covers the linked archive codec. Fresh
assembly construction and native application validation have separate gates.

[Field order and measured cases](../../../../../re/solidworks/records/SdkAssemblyHistoryComponent2026.md)
· [Hash-bound receipt](../../../../../re/solidworks/measurements/2026/SdkAssemblyHistoryComponent01.json)

# Normal SDK writing for ordinary planar assemblies

The SOLIDWORKS writer accepts complete neutral assemblies with one owned
dimensioned rectangular part and two or three direct occurrences. Default
`.SLDASM` selection and explicit `solidworks.sldasm` use the shared SDK
compiler and publish the parent plus its owned child.

Provide an actual absolute Windows target, or a physical host target with an explicit `native_destination` mapping. All authored filenames must agree. The bounded profile preserves ordered principal-plane coincident/parallel and positive distance mates, active configurations, real endpoint owners, fixed anchor and child drivers. Unsupported models, incomplete dependencies and unprojected fields are rejected. No external source file is read to generate output.

Write to unused parent and child filenames on the filesystem. Ordinary
filename conflicts and handled second-publication failures preserve existing
entries. A concurrent child created during publication raises
`FileExistsError` and keeps its data. A separate actual Windows process
produced both files from the neutral document using its native destination.

Twenty-nine host and two Windows process checks passed. Both normal
registry selection methods reproduce the exact native-tested files.
Three standalone part profiles retain their bytes and strict readback
JSON. The writer checks recorded zero runtime input reads and no CAD
activation. The earlier SOLIDWORKS lifecycle provides the vendor evidence.

[Native lifecycle](../../../../../re/solidworks/records/SdkPortableAssemblyRegistryNative2026.md)
[Current process receipt](../../../../../re/solidworks/measurements/2026/SdkDefaultAssemblyPublication01.json)

[Usage and supported scope](../../../../Reference/Adapters/SolidworksAssemblyWriting.md) · [Exact source and process receipt](../../../../../re/solidworks/records/SdkAssemblyPublicRegistration2026.md)

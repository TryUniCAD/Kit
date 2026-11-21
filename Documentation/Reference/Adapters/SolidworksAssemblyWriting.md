# Writing ordinary native SOLIDWORKS assemblies

The assembly writer takes a complete neutral `CadDocument.assembly` and generates the native root `.SLDASM` and its owned dependencies beside it. The neutral documents and occurrence graph provide the inputs to the shared SDK constructors.

The flat mate profile uses two or three direct occurrences of one owned dimensioned rectangular part. It supports aligned ordinary coincident/parallel and positive driving distance mates between actual principal planes. It preserves the authored names, active configurations, ordered occurrence/plane references, fixed anchor, rigid placements and rectangular child dimensions. The initial placements must satisfy every mate. Unsupported features, mates, child shapes, suppressed/hidden/flexible instances, unresolved references, extra metadata and incomplete ownership fail closed.

An occurrence may carry an explicit `reference_number` such as `"2"` for `SharedPart-2`. It must match the canonical positive decimal suffix of the occurrence name. Leave the field empty to derive the same native number from the name. [Occurrence reference numbers](../../Changes/Solidworks/Construction/Assembly/SolidworksOccurrenceReferenceNumbers.md)

For two direct occurrences, the writer also accepts one ordinary perpendicular mate between principal planes. Use one fixed occurrence, unknown alignment and an initially orthogonal placement. This profile excludes other mates in the same group and active correction from an invalid angle. The normal mate reader preserves the ordered references in native saves. [Perpendicular qualification](../../Changes/Solidworks/Archive/Assembly/Groups/SolidworksPerpendicularRegistryQualification.md)

The rigid nested profile uses a complete acyclic hierarchy with separately owned rectangular blind-boss parts and explicit selected configurations. Floating rigid occurrences retain their local transforms and repeated instances share one generated child. A leaf may carry the ordinary driving depth or the depth plus driving width and height with the prescribed rectangle relations. The nested profile accepts a hierarchy without mates, suppression, hidden instances or flexible placement. [Nested writing and native qualification](../../Changes/Solidworks/Construction/Assembly/SolidworksRigidNestedAssemblyWriting.md)

`convert.write_document` selects the writer by `.SLDASM` destination
or explicit `destination_format="solidworks.sldasm"`. The assembly
alias resolves to the canonical `solidworks.sldprt` registration.

On Windows, provide the actual absolute final path. That path establishes the directory for every native file identity. On another host, provide the physical final destination plus the explicit corresponding Windows `native_destination` in write values. The staged, physical and native assembly basenames must match the neutral root name. Each validated owned definition name supplies one sibling filename.

```python
from pathlib import Path
from convert import write_document

result = write_document(
    document,
    Path(r"C:\Generated\AssemblyName.SLDASM"),
    destination_format="solidworks.sldasm",
    allow_carrier=False,
)
```

For a mapped host path, add `values={"native_destination": windows_parent_path}`.
The native Windows path supplies the mapping directly. The Windows process
verified this path with both files generated and zero runtime input reads.

Output must use unused parent and companion filenames. Assembly overwrite and
stream output are unsupported. Existing files, directories and dangling
symlinks are conflicts, including case variants. Each file is published
exclusively. If another process creates a companion during publication, the
call raises `FileExistsError`, keeps the peer's file and rolls back outputs
that belong to the current write. [Registry path behavior](../Architecture/Engine.md#path-destinations)

The result path and `bytes_written` describe the requested assembly.
Metadata additionally reports `component_file_count`, `component_file_names`,
`component_bytes_written` and `bundle_bytes_written`. Native usability flags
apply to the measured SOLIDWORKS 2026 profile.

The default public route reproduces both exact files from the disclosed native lifecycle trial at matching inputs, path, epoch and interpreter. Separate processes preserve prior polygon and both qualified circle writer/readback outputs, exercise real registry selection, and reject unsupported or conflicting requests. Two original perpendicular pairs also passed the normal registry native evaluation through reorientation, child depth edits, save and fresh reopen. [Perpendicular native evidence](../../../re/solidworks/records/PerpendicularRegistryAccepted2026.md)

[Native lifecycle evidence](../../../re/solidworks/records/SdkPortableAssemblyRegistryNative2026.md) · [Registration evidence and limits](../../../re/solidworks/records/SdkAssemblyPublicRegistration2026.md) · [Change entry](../../Changes/Solidworks/Construction/Assembly/SolidworksPublicAssemblyWriting.md)

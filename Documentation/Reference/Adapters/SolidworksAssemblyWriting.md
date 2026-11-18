# Writing ordinary native SOLIDWORKS assemblies

The bounded assembly writer accepts a complete neutral `CadDocument.assembly` with one owned dimensioned rectangular part and two or three direct occurrences. It writes a native `.SLDASM` plus that part's `.SLDPRT` beside it. Both files are generated from the neutral model through the shared SDK constructors. Existing external part files are not writer inputs.

The supported group contains aligned ordinary coincident/parallel and positive driving distance mates between actual principal planes. It preserves the authored names, active configurations, ordered occurrence/plane references, fixed anchor, rigid placements and rectangular child dimensions. The initial placements must satisfy every mate. Unsupported features, mates, child shapes, nested components, suppressed/hidden/flexible instances, unresolved references, extra metadata and incomplete ownership fail closed.

`convert.write_document` selects the writer by `.SLDASM` destination
or explicit `destination_format="solidworks.sldasm"`. The assembly
alias resolves to the canonical `solidworks.sldprt` registration.

On Windows, provide the actual absolute final path. That path establishes both native file identities. On another host, provide the physical final destination plus the explicit corresponding Windows `native_destination` in write values. The staged, physical and native assembly basenames must match the neutral root name. The validated owned child name supplies its sibling filename. The SDK does not guess a drive mapping or resolve a source-file reference.

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

The default public route reproduces both exact files from the disclosed native lifecycle trial at matching inputs, path and epoch. Separate processes preserve prior polygon and both qualified circle writer/readback outputs, exercise real registry selection, and reject unsupported or conflicting requests. This registration adds no new native batch or held-out credit.

[Native lifecycle evidence](../../../re/solidworks/records/SdkPortableAssemblyRegistryNative2026.md) · [Registration evidence and limits](../../../re/solidworks/records/SdkAssemblyPublicRegistration2026.md) · [Change entry](../../Changes/Solidworks/Construction/Assembly/SolidworksPublicAssemblyWriting.md)

# Writing ordinary native SOLIDWORKS assemblies

The assembly writer takes a complete neutral `CadDocument.assembly` and generates the native root `.SLDASM` and its owned dependencies beside it. The neutral documents and occurrence graph provide the inputs to the shared SDK constructors.

The normal flat writer supports the exact measured coincident and
driving-distance pair. It uses two direct occurrences of one owned
dimensioned rectangular part and one fixed occurrence. The child,
configuration, names, placements and actual principal plane selections
come from the neutral graph. The ordered mate group and three child
drivers remain editable. Other planar and perpendicular profiles have
independent internal construction and native evidence.
[Scoped measurement and limits](../../../re/solidworks/records/AuthenticatedPlanarBundle2026.md)

An occurrence may carry an explicit `reference_number` such as `"2"` for
`SharedPart-2`. It must match the canonical positive decimal suffix of
the occurrence name. Leave the field empty to derive the same native
number from the name. [Occurrence reference numbers](../../Changes/Solidworks/Construction/Assembly/SolidworksOccurrenceReferenceNumbers.md)

The rigid nested profile uses a complete acyclic hierarchy with separately
owned rectangular blind-boss parts and explicit selected configurations.
Floating rigid occurrences retain their local transforms and repeated instances
share one generated child. Each leaf has the measured driving depth, with
optional driving width and height in the prescribed rectangle profile.
The writer verifies every member against an authenticated whole-bundle
measurement. [Nested publication scope](../../Changes/Solidworks/Construction/Assembly/SolidworksAuthenticatedNestedBundle.md)

`convert.write_document` selects the writer by `.SLDASM` destination
or explicit `destination_format="solidworks.sldasm"`. The assembly
alias resolves to the canonical `solidworks.sldprt` registration.

For the measured planar pair, pass the released
`MeasuredOutput.json` file's `measurement` member in
`values["solidworks_native_measurement"]`. Use the receipt's exact
encoded assembly locator. On macOS also pass it as the explicit
`native_destination`. The final filesystem path must correspond to
the measured locator for a native-usable result.

```python
from convert import write_document

result = write_document(
    document,
    physical_final_path,
    destination_format="solidworks.sldasm",
    allow_carrier=False,
    values={
        "native_destination": measured_native_parent,
        "solidworks_native_measurement": report["measurement"],
    },
)
```

To deliver the exact same pair to a separate physical directory for
later installation at that locator, also pass
`values["defer_native_delivery"] = True` and allow the non-qualified
result with `allow_carrier=True`. Kit verifies the same file hashes,
reports `required_native_destination`, and leaves both native usability
flags false for the deferred files.

The nested route uses the same options with its whole-bundle evidence
envelope. Set `written_at` to the measured epoch and give its `receipt`
the schema `kit.sw2026.rigid-nested-bundle-evidence.v1`. Supply the agreed
`generated_manifest_sha256` and `native_result_sha256` from the approved
bundle measurement. Each measured nested member must match before the
same-location or deferred publication policy can apply.
[Nested evidence](../../../re/solidworks/records/AuthenticatedNestedBundle2026.md)

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

The measured planar public route reproduces both complete files from
the disclosed native lifecycle at the encoded path and epoch. It
requires a registry-owned stage. The strict reader retains the actual
live distance parameter and its ordered selections after the write.
[Authenticated planar change](../../Changes/Solidworks/Construction/Assembly/SolidworksAuthenticatedPlanarBundle.md)

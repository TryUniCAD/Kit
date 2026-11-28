# Constructed file handles use typed text

Expected: a shared file identity reader accepts the actual handles produced by
the fresh SDK file constructor, as well as equivalent decoded header/body
handles.

Actual: `MakeFileDef` constructs `moCStringHandle_c.value` as `CStringValue`.
Header decoding also exposes `text`; body decoding exposes `f08`. The mate
file-key helper previously accepted only the decoded string fields, so an
actual SDK `PartCandidate` failed before the first complete assembly could
validate its child identity.

The helper now accepts the existing typed string owner and requires every
present representation to contain the same nonempty text. Conflicting,
missing, empty or untyped fields reject. New parent-owned shared handles can
expose consistent header/body views on one actual node without mutating the
child or adding a wire field.

The complete guarded assembly process exercises four valid representations
and five malformed variants. Eighteen generated bundles and twelve historical
bundle regressions also preserve their exact emitted streams. No native
measurement is inferred from this representation repair.

[Construction record](../../../../../../re/solidworks/records/SdkCompleteAssemblyConstruction2026.md) ·
[Process receipt](../../../../../../re/solidworks/measurements/2026/SdkCompleteAssemblyConstruction01.json)

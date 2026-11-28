# Authored scene on a generated SOLIDWORKS local import

Task `B04-SW2026-IMPORTED-BODY`, PR #121. Build a planar imported solid
with the actual source's supported light semantics, using one ordered
ambient and directional group. Scene values come from the source being
projected. The constructor uses the existing feature allocator and
light serializers. It never looks up station defaults or reads an archive.

## Locked disclosed trial

The [trial tool](../../tooling/sw2026/imported_body_source/ProbeImportedPartScene.py)
pins the original disclosed imported rectangle, the independent translated
rectangle and the separate Unicode feature rename by SHA-256. The inputs
first pass the strict geometry, name and scene ownership checks. The expected
geometry comes from the original authoring specifications. Frozen processes
construct the same bytes twice with zero runtime file reads.

A second construction at each destination with no light values changes
only `Header2`, `Contents/CMgr`, `Contents/Config-0` and its ModelHeader and
ResolvedFeatures. Light semantics agree by typed readback. The scope includes
the actual import feature and bound body label, the active configuration
name, the closed planar boundary and the four lights. The original explicitly
empty property owner records are absent in the generated read. Source identity,
provenance and additional presentation owners remain outside this check.

The native protocol compares each source, rebuilt candidate and independently
reopened save in fresh processes bracketed by known-good controls on build
`34.5.2.0604`. Native scene names and ownership are observed cold and after
rebuild. All eleven fresh processes passed. Three generated candidates
passed clean open, rebuild, save and fresh reopen through 348 geometry
comparisons. Typed save readback preserved all 192 authored light values.
These are disclosed discovery inputs. Held-out and public writer
qualification remain separate.
[Native part scene receipt](../measurements/2026/ImportedLocalSceneNative01.json)

The first frozen packet `893c11258cd5f61f3e50547a76397e089c11c5675327e3f364b90d0e1a2996ae`
stopped before COM with a manifest-key mismatch. Its host used forward
slashes and the guest compared native path separators. The retry uses
portable archive keys while retaining native output paths.
[Existing manifest gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Extrusion/FrozenManifestKeysUsePortablePaths.md)

## Empty notes and ordered feature tree

The same three disclosed inputs also supply the actual annotation cabinet's
reciprocal empty notes pair. The writer builds the two owners beside the
authored lights from typed captions and chronology. At each destination,
adding the pair changes five logical streams. The independently generated
baseline keeps the same configuration, geometry and file property owner.

The generated files pass 348 geometry comparisons through cold open,
rebuild, native save and independent reopen. Both controls pass across
eleven fresh processes. All three 24-row cold feature trees match their
respective originals. Both notes match in the source, generated and
reopened trees, including after rebuild. Each native save keeps both
typed captions and chronology, 64 light values, three empty property
scopes and the 102-byte file property owner. This disclosed trial leaves
complete original-source admission and public writer qualification open.
[Native notes receipt](../measurements/2026/ImportedPartNotesNative01.json)

## Empty exploded-view manager

A separate frozen comparison constructs the concrete empty part manager
from explicit presence. Its keyword binds to its generated persistent
ID. The manager starts in Config-0 and remains inherited by the actual
resolved map. Three native saved derivatives retain the manager and its
persistent identity. Their save allocation can move its archive map
index. Both controls pass across eleven processes, with 348 candidate
geometry checks and matching cold trees.
[Disclosed manager result](../measurements/2026/ImportedPartExplodedNative01.json)

The annotation profile repeated that comparison against both original
inputs in the pre-writer locked cohort. Each generated and native-saved
part has the same ordered 24-row cold tree as its source, both note
owners with their recorded chronology, the empty exploded manager, and
the previously qualified lights and property owners. Both controls pass
across eight fresh processes and all 232 candidate checks pass.
Complete original-source transfer and public writer qualification remain
open. [Locked annotation result](../measurements/2026/SealedImportedAnnotationManagers01.json)

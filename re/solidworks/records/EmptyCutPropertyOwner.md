# Source-bound empty cut-list property owner

Task `A12b-EmptyPropertyOwner` owns this research-only producer, consumer and proof. The encoder boundary lane owns delivery on base `511263a22ca10688929e49bdf8def74966bf1433` from PR #319. PR #121 retains the property grammar and production implementation. This tranche ends with a qualified property-substream round trip; it emits no `.SLDPRT` container and establishes no native or full-source acceptance.

## Explicit request and scope

The request has exactly two fields: `schema: kit.research.empty-cut-property-owner.v1` and Boolean `empty_cut_owner`. Both [absent](../PropertyBoundary/Requests/Absent.json) and [present](../PropertyBoundary/Requests/Present.json) requests require a concrete key-zero container and file owner with empty document/configuration lists. The Boolean selects a null cut-list pointer or a fresh concrete cut-list owner with two empty collections. All three literal XML scopes are explicitly empty under this request profile. Strings, native slots and captured data cannot be supplied.

The generator reuses the exact PR #121 typed `MakePropContext`, `BodyWriter`, property layouts and empty-owner guard at `c0a401a607759fb0c2589647c2a22af65ebb7ce1`. SDK imports and text codecs initialize before the in-memory construction guard. The guarded phase builds fresh nodes, derives counts and tags, serializes the property stream, and reads it back. It permits no file, process, network or dynamic-library access. Generation takes no source path.

Readback checks the complete manager fields, one actual key-zero row, distinct container/file owners, exact cut-pointer presence and empty collections. It also verifies exact re-emission and each object's archive slot. Empty-policy acceptance alone cannot establish those facts. [Owner-presence gotcha](../../../Documentation/Gotchas/Research/Writers/SolidworksEmptyPropertyGuardDoesNotProveCutOwnerPresence.md)

## Source to JSON to generated substreams

Use Python 3.14.6 and a clean checkout at the pinned PR #121 revision. Keep inputs and outputs private. `$tool` names the tracked command, `$reader121` the dependency checkout, `$source` the already disclosed Author04 baseline and each output variable an unused directory.

```powershell
$tool = 're/solidworks/PropertyBoundary/EmptyCutPropertyOwner.py'
python -I -B $tool extract --source $source --source-sha 02cc9e0ea4b2cebe3b99d908180b409f1ceeffd5cbef13d2a9685caaf4d8ca7d --dependency-root $reader121 --output $projected
python -I -B $tool generate --request "$projected/Request.json" --dependency-root $reader121 --output $generated
python -I -B $tool generate --request re/solidworks/PropertyBoundary/Requests/Absent.json --dependency-root $reader121 --output $fileOnly
python -I -B $tool compare --generated $generated --source $source --source-sha 02cc9e0ea4b2cebe3b99d908180b409f1ceeffd5cbef13d2a9685caaf4d8ca7d --dependency-root $reader121 --output $compared
```

`extract` verifies the source digest, actual version-19000 property graph and all three empty XML scopes. It emits only the tiny request and separate source evidence. It refuses absent keyed file ownership, populated/unknown owners or authored text. Its request is byte-identical to the independently authored present request, SHA-256 `45ba35ff0c0e7c501ad6f9620920c7491a14eb7157e3d2fe2e487f248c9d63a9`.

`generate` consumes that persisted JSON alone. Its output is `Properties.bin`, three XML members, the retained request and evidence. These are individual substreams, not a native part. `compare` verifies the generated custody and typed graph before reading the original as an optional independent comparator. It records differences rather than changing generation.

## Actual evidence and limits

The file-only stream is 102 bytes, SHA-256 `22ecc7dd4564532e71f54ca4b59e9aee9c6e98c62a2f9c7fecc6fe72d793134e`, identical to the existing `WriteEmptyProps` golden. Its next map slot is 7. Adding the concrete empty cut owner produces 138 bytes, SHA-256 `9fd3dc57a5b385acbbd4b0f36fffec581481014616bb254a4f417f3537c1f036`, exactly the independently retained source property stream, with next slot 9. The three generated XML members are byte-identical between variants. The source custom/configuration XML also match exactly; the source core XML differs, although the supported authored summaries are empty. Original core provenance is not preserved by this request. [Recorded proof](../measurements/2026/EmptyCutPropertyOwner.json)

The final extractor and three generation processes ran separately. The two final present-generation reports are byte-identical, SHA-256 `b2259e61e58fdf71b2d5ea33c32d650b4f989d76ec656b378a4c0cff443639c3`. The optional comparison confirmed the source stream and owner slots. An integer presence request and an inexact source digest each exited 1 before creating output. Earlier source-independent feasibility retained the same root/container/file objects while changing only the cut pointer, and the existing typed guard refused populated and wrong-class cut owners before emission. Its distinct method and report hashes remain identified in the proof.

The private holder `EmptyPropertyOwner01` retains both feasibility runs and `Consumer01` inputs, generated substreams, extractor/comparison evidence and boundary logs. The exact original is already retained in the separate renderer recovery bundle, member `Native/Author04.SLDPRT`, SHA-256 `02cc9e0ea4b2cebe3b99d908180b409f1ceeffd5cbef13d2a9685caaf4d8ca7d`; that private bundle has SHA-256 `2e5785fe96fb97c8766ff697ec9f41be7230752058f0c9acc5c3b3b1d2477856`. No native file, source header or raw path is tracked here.

The existing [PR #121 property study](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/re/solidworks/records/PartEmptyAdvancedProperties2026.md) owns broader semantics. This study neither promotes a production flag nor treats null and concrete empty owners as interchangeable. Part-container integration, native preservation, other property profiles, original metadata and held-out generalization remain open.

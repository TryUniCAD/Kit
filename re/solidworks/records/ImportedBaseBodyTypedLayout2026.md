# Typed ordinary imported base-body layout

The shared ResolvedFeatures codec reads and re-emits `moBaseBody_c` schema 1
for the ordinary SOLIDWORKS 2026 SP05.2 part archive. It requires version
19000 and the linked flags `model_is_part`, `model_compressed_stream` and
`cmgr_f658` all equal to one. The graph obtains these flags from the actual
configuration and configuration manager. The grammar admits the local-body
route and refuses every other signed switch value before reading its
mode-specific suffix.

The [native owner record](ImportedBaseBody2026.md) binds the class to the
exact `sldmopartu.dll` wrapper at `0x1802fcb70` and its shared import
serializer at `0x1802fd060`. The typed class uses the existing
`moBodyFeature_c` trunk. It contributes the measured concrete virtual
slots to the shared resolved table.

| Slot | Resolved behavior |
| --- | --- |
| `0x3e8` | `moFeature_c.SerializeXmlData` |
| `0x3f8` | Publish the actual node key for XML |
| `0x4b8` | `moConcept_c.SerializeLWData` |
| `0x4c0` | `moConcept_c.SerializeResolvedData` |

## Local suffix

| Wire order | Modeled field | Ownership |
| --- | --- | --- |
| CString | `source_filename` | Optional input name from the import object. The codec retains it as text and performs no filesystem lookup. |
| Signed i32 | `local_body_switch` | Native storage selector. This grammar admits exactly one. |
| CString | `local_storage_key` | Literal key for the separate LocalBodies group. It remains a separate field from the feature name and body atom label. |
| Signed i32 count and signed i32 rows | `segment_mesh_count`, `segment_mesh_ids` | Ordered feature IDs. The shared array writer derives the count from the rows and preserves their order. |

Both text fields use the shared CString codec, which retains the Unicode or
ANSI frame type. Every source in this measurement has a Unicode empty source
filename, a Unicode local key and an empty segment-mesh vector. The array
grammar follows the measured vector producer and its exact static loop. A
native part with segment-mesh rows remains outside the measured solid-body
scope.

## Observed linked replay

Two offline processes read the four hash-verified, disclosed native
originals with `ReadNativeLink`. Each replay used the production
classification, virtual and field tables with the actual configuration map
and manager context. Each build reproduced all five streams byte for byte
and matched the prior native receipt digests.

| Disclosed case | Local storage key | Explicit atom label | Resolved map base → final |
| --- | --- | --- | --- |
| Original | Imported1 | absent | 107 → 180 |
| Other shape | Imported1 | absent | 107 → 180 |
| Renamed feature | Transfer Δ17 | absent | 107 → 180 |
| Renamed body | Transfer Δ17 | Casting Ω72 | 108 → 181 |

The five streams for each source are Config-0, ResolvedFeatures, CMgr,
ModelHeader and Header2. The first source also provides refusal controls
through the same production entry points. Both reader and writer refused
manager mode zero. The writer refused route words zero, two and minus one
and a schema-two descriptor. The process guard allowed ordinary module
setup before measurement and denied any file or process access during the
linked parse and re-emission. Both successful runs had zero denied events.
[Unpatched measurement](../measurements/2026/ImportedBaseBodyTypedReplay01.json) · [Prior witness](../measurements/2026/ImportedBaseBodyWitnessReplay01.json) · [Disclosed contrasts](../measurements/2026/ImportedBodyNamesContrast01.json)

## Reproduce the typed comparison

```sh
PYTHONPATH=src:. uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/ReplayTypedBaseBody.py \
  --disclosed "$DISCLOSED_PART" --other-shape "$OTHER_SHAPE_PART" \
  --renamed-feature "$RENAMED_FEATURE_PART" --renamed-body "$RENAMED_BODY_PART"
```

The operator verifies the four disclosed source hashes before parsing
and prints the numeric receipt. The preservation proof covers the linked
archive grammar. Local-body payload construction, application-qualified
imported-body writing and public conversion acceptance remain open.

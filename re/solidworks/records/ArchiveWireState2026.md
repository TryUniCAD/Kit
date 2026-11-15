# SOLIDWORKS 2026 wire state and canonical save fields

Status: **partial**. This table records 2026 binary reads and writes. It does not
establish held-out byte identity, a fresh-model builder, or vendor acceptance.
Kit still has no SOLIDWORKS writer.

## Evidence identity

The [2026 manifest](../v2026/Manifest2026.json) records the binary hashes.
The addresses below are the 2026 SP05.2 images, not relocated 2025 addresses.
Local decompile exports remain in the untracked `sw26gh/out/` workspace.
No decompiled source is included here.

## Field classification candidates

| Record and wire field                      | Wire type                         | Role for synthesis        | Rule or open question                                                                                                     | Binary evidence                                                                           | Status    |
| ------------------------------------------ | --------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | --------- |
| `moGtolItemTol2022_c.f18#0`                | i32                               | derived alias             | Equal to the final `f18` member during a canonical save; preserve each original slot for source byte identity             | `sldmfcu` `0x3c85e220`, `cfg_gtol22.c` reads 140–141, writes 217–218                      | partial   |
| `moSwiftGtsOptions_c.f220#0/#1`            | i32                               | derived aliases           | The save writes the same member three times; the first two positions are not independent inputs                           | `sldmfcu` `0x3c83c760`, `cfg_ddsub.c` reads 2122/2131/2140, writes 2354/2363/2372         | partial   |
| `moLightFeature_c.f384#0`                  | i32                               | derived alias             | Duplicate of `f384` in a canonical save; semantic meaning of the underlying member remains unresolved                     | `sldmodu` `0x4bc0b030`, `cfg_lights.c` writes 125–127                                     | partial   |
| `moAnnotationView_c.f3e8#0`                | object tag                        | derived reference         | Same graph node as the later `f3e8` on save; reference indices derive from serialization order                            | `sldmodu` `0x4c217100`, `cfg_big.c` writes 2692/2695                                      | partial   |
| `moLightFeature_c.f36c`                    | i32                               | volatile candidate        | The loader consumes the scalar and clears the runtime member; zero is a candidate, not yet an oracle-proven neutral value | `sldmodu` `0x4bc0b030`, `cfg_lights.c` reads 192–194, writes 115–116                      | partial   |
| model `has_fdb8`                           | i32                               | derived presence          | Canonical save emits zero or one from member presence; load accepts any nonzero flag                                      | `sldmodu` model restore `0x4c234150`, `cfg_part_deep.c` reads 2637–2644, writes 2848–2853 | partial   |
| model `has_f1270`                          | i32                               | derived presence          | Print-settings presence; print-record fields still require separate classification                                        | `sldmodu` model restore `0x4c234150`; print body load `0x4b541b90`, store `0x4b541c40`    | partial   |
| part `has_f16b8`                           | i32                               | derived presence          | Depends on both `f16b8` and `f16d0` maps; existence of one field is insufficient to infer the canonical flag              | `sldmodu` part restore `0x4c2378b0`, `cfg_part_deep.c` 350–416                            | partial   |
| `moGhostBodyObject_c.has_f50`              | i32 plus conditional object tag   | derived presence          | Emit the object tag whenever the wire flag is nonzero, including a null object tag                                        | `sldmodu` `0x4bf05390`, `cfg_t2a.c` 125–145                                               | partial   |
| part mass-cache count and `f1628`          | i32 plus records                  | derived cache bookkeeping | Canonical storage holds at most two cache records; count derives from the cache set, not a saved case                     | `sldmodu` part restore `0x4c2378b0`, `cfg_part_deep.c` 250–291                            | partial   |
| part `f1638`                               | i32 when cache count exceeds one  | unresolved selector       | Meaning and generation rule are not established                                                                           | same part restore                                                                         | not found |
| part bounding-cache count and `f1640` keys | i32 plus ordered key/object pairs | derived cache bookkeeping | Preserve count, keys, order and null tags; canonical cleanup is not yet understood                                        | load `0x4b797c20`; store `0x4b797cf0`; cleanup `0x4b7975f0`                               | partial   |

All rows are within `Contents/Config-0`; configuration numbering can vary.
The table contains no proven constants and supplies no per-document defaults.
It is a subset of the required field classification, not a completed register.

## Codec boundary

The source codec preserves wire observations separately from runtime fixups.
For constructed records, duplicated aliases use their canonical graph member.
Presence flags can be supplied explicitly when their complete semantic predicate
is not recovered. Missing fields still fail; the codec does not invent their values.
Negative or greater-than-two mass-cache counts are rejected instead of truncated.
Bounding-cache entries are retained rather than silently filtered.

`FieldScan.py` reports values invariant within the sampled inputs as
`sample-invariant`. This does not prove that a field is a format constant.
Unrelated designs and a format explanation are still required for that classification.

The next evidence gate is remote byte identity on the eight redacted ladder controls.
Those controls were used in schema research and are not held out.

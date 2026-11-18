# Drawing view rendering state in SOLIDWORKS 2026

Both disclosed original drawings still fail normal Definition admission at `blank drawing Definition excludes sheet annotations`. This tranche preserves two understood view-state fields; it does not qualify the complete original drawings or their writer.

Task `B04-SW2026-DRAWING-VIEW-RENDERING`, owner PR #121 drawing-reader lane, delivery PR #121. The dependency is the independently verified detailing-index reader. The scoped exit is typed rendering retention, exact raw stream/map/identity preservation, unchanged prior profiles, and explicit unprojected colour associations. The broader CAD success criteria remain unmet.

The [machine-readable native proof](DrawingViewRendering2026.json) and [sanitized process receipt](../measurements/2026/DrawingViewRenderingRead01.json) bind the exact source and measurements. The earlier [absolute-view field ledger](DrawingAbsoluteViewFields2026.md) describes fresh generated state; it must not replace retained state when reading a saved source.

## Exact native owner

All addresses refer to `sldmodu.dll`, version 34.5.2.604, 46,536,280 bytes, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. The original PE is external licensed research material. No vendor image or instruction listing is included.

| Function | Complete range | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `moAbsoluteView::Serialize` | `[0x4c94bfa0,0x4c94c1a4)` | 516 | `9cde5993ba41117ac61b78c8807d0a8d9e9c714469836169b00ecdba50a1477c` |
| `moDrView::Serialize` | `[0x4c958dc0,0x4c95d339)` | 17785 | `b1018566bae23e886645bb5ffcc13ee501f2f6a0bd57fb041f9a1f4c516d2656` |
| Sketch-cache body helper | `[0x4c54fe50,0x4c550101)` | 689 | `830e867eb551504651113f034f68733ffe3347b09d33d95c683fe9947a2799af` |
| Occurrence-colour map getter | `[0x4b288330,0x4b288338)` | 8 | `a15aa89e1dca0091861c4d62202f55c552658494cbf26342962ccf5f72320fe1` |
| Occurrence-colour map clear | `[0x4b2820e0,0x4b282158)` | 120 | `c8991672198ab853d19326ba05bb6154c6d48149021225e77b5fe5e231a6561b` |

The exception directory supplies complete bounds for the four non-leaf entries. The getter is an independently decoded complete leaf. Direct RTTI and vtable reads bind `moAbsoluteView` vtable `0x4ce83fb8` slot `+0x28` to `0x4c94bfa0` and `moDrView` vtable `0x4d2713f0` slot `+0x28` to `0x4c958dc0`. These hashes and cells were rechecked against original file bytes. Static inspection does not imply native execution.

## Field rules

| Field | Encoding and rule | Ownership and classification | Confidence |
| --- | --- | --- | --- |
| `has_fb50` | One unsigned byte, computed by native store as `view+0xb50 != null`; selected admission requires exact integer 0 or 1 | Retained pointer state of the actual `moDrView`, not an annotation count | Confirmed native boundary |
| `fb50.n` | Signed 32-bit saved cache-record count; selected admission requires exactly zero | Derived native count; retained separately from pointer absence | Confirmed empty-body boundary |
| `nf68` | Signed 32-bit row count, derived from actual `ff60` rows; an explicit stored count must agree | Bookkeeping | Confirmed native boundary |
| `ff60[].key` | Signed 32-bit integer | Native occurrence number from `getOccNumToCompColorMap`, retained from source | Confirmed native type; portable join partial |
| `ff60[].value` | Unsigned 32-bit integer | Native colour word retained from source without RGB reinterpretation | Confirmed native type; portable appearance partial |

At `0x4c9597ad`, native store emits the cache pointer-presence byte. A present pointer reaches `0x4c54fe50` at `0x4c9597c2`. The read path is admitted from effective version `0x2ee`: `0x4c95b3ca` reads presence, then allocates a 16-byte non-tagged state, puts the actual view pointer at `+0`, clears the record-container pointer at `+8`, installs it at `view+0xb50`, and calls the same helper at `0x4c95b403`.

The helper stores zero when there is no record container. Otherwise it counts only 40-byte internal records with state `+0x18 == 0`. A saved zero count therefore does not prove that the runtime container had no internal records. On read, a nonpositive count returns without reading record bodies; selected SDK admission accepts exactly zero and rejects negatives and populated counts. A present empty body adds no class/object tags or archive-map entries. The outer 16-byte state has no claimed runtime class or vtable. The actual positive-record type `moDrSgProp_c` has vtable `0x4d1c06e8`, slot `+0x28 -> 0x4c956f90`; its populated grammar and semantic projection remain outside this profile.

The exported map getter at `0x4b288330` returns `this+0xf60` with native signature `std::map<int,unsigned long>`. Native store writes count at `0x4c959bb5`, key at `0x4c959bd6`, and unsigned colour word at `0x4c959be2`. Native read reaches this map from effective version `0x11b5`, with count/key/value reads at `0x4c95c636`, `0x4c95c66f`, and `0x4c95c67c`. These rows contain no archive object/class tags. The SDK retains order and exact words, requires unique keys and consistent counts, and rejects unknown row fields. It does not resolve an occurrence key to a child component or interpret the colour word as RGB.

## Actual SDK boundary

[ReadRenderState](../../../src/convert/adapters/solidworks/Drawing/Definition/Rendering/ReadRenderState.py) requires ordinary archive version 19000 and a concrete schema-one `moAbsoluteView`. [ReadGraphRender](../../../src/convert/adapters/solidworks/Drawing/Definition/Rendering/ReadGraphRender.py) follows the actual drawing, active sheet and sole absolute-view aliases. It does not select a guessed object index.

[RenderState](../../../src/convert/adapters/solidworks/Drawing/Definition/Rendering/RenderState.py) distinguishes absent cache from present cache with zero saved records. [ReadOccColours](../../../src/convert/adapters/solidworks/Drawing/Definition/Rendering/ReadOccColours.py) exposes signed native keys and unsigned native values. `NamedRead.Rendering` and `FrontRead.Rendering` retain the actual view object. Nonempty native colour rows add `drawing.occurrence_colours` to `Unprojected`; existing `drawing.detailing_edges` remains separate.

Only `has_fb50_equals_zero` and `ff60_empty` are replaced with these typed rules. The other 29 view-state predicates and all other graph guards remain unchanged. The existing field layouts and serializers do not change. No constructor state, saved row, colour constant or whole-word default is introduced. The original frozen drawing composer, public adapter registration and original held-out verdict remain unchanged.

## Verification and remaining work

Root independently ran the exact 4,379-source candidate. All 43 prior workers passed: 18 disclosed generation/comparison workers and 25 unsupported-job workers. The bounded preservation process passed both originals' complete raw Definition byte, map and object-identity comparisons, with zero unread tails. Each actual view retains pointer presence, zero saved cache records and its native colour row. Every occurrence key and colour word is compared to its actual source row.

Sixty malformed full-`WriteNamedDef` cases reject cache presence/body/count, colour row/count/type/domain, unknown fields and duplicate keys before returning a result. Three authored variants run through complete normal Definition write/read/store on the qualified generated Front control: absent cache, present empty cache, and independently authored signed-key/unsigned-word boundaries. These are process proofs, not native measurements.

Both original normal Definition reads retain the exact sheet-annotation rejection. Positive source semantic admission, portable component-colour projection, full original writer equivalence, native acceptance and held-out acceptance remain false. The next work is the actual nonempty `moDetailFolder_c` collection and its concrete owner; its current guard is preserved.

The executed candidate01 manifest is `5f6b43a082bf80a60914d5a0b5c3b8f85fcc67c2348d33bd7120f54e421f607c`. Corrected metadata candidate02 is `0864aa1eea2352baba379a7f5acb1f0a45be0db63531aa1cd79e4e149990bbe3`. All 4,379 complete source-file rows are identical. Candidate01 inherited the prior tranche's 16-path `reader_delta_paths` label; candidate02 correctly names this 15-path rendering delta. This is a metadata correction, not a distinct product run. The raw execution report is `f8aff7fe71fec95d5dde4deeab8d18f91c10b719a233bbd5d4b8cc0c83f53ef0`; prior 43-worker report is `8b84da1ecc5c090c595e07ae30bb48d545e048686a2ee9bef612ea63c1501268`.

The mandatory stopping conditions remain: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This scoped handoff does not mark the broader CAD goal complete.

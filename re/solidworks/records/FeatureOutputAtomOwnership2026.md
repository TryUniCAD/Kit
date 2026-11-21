# Ordinary feature output atom ownership, SOLIDWORKS 2026

This checkpoint proves separate ownership of saved atom IDs, created atom objects, and live bodies. It does not qualify a generated part or identify a measured same-invocation cause of empty public body inventory.

Task `B04-SW2026-ORDINARY-PART-PARTITION-LOAD`; owner `/root/flag_ownership`; delivery PR #121. Dependencies are the existing shared archive object maps, current Resolved layouts and the immutable [atom-manager enumeration checkpoint](AtomManagerBodyEnumeration2026.md). The checkpoint exits with independently replayable source rules and numeric observation boundaries; native construction and acceptance remain root-owned.

## Exact build and scope

- SOLIDWORKS 2026 SP05.2, file version `34.5.2.0604`, AMD64.
- `sldmodu.dll`, preferred base `0x4b140000`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
- `sldmfcu.dll`, SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`.
- `swccu.dll`, SHA-256 `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c`.
- Selected ordinary archive version `19000`, context conditions `0`, archive helper `+0x874=0`, non-DB archive mode, concrete `moExtrusion_c`. A feature's actual creation version is a separate value from the enclosing file version.

The [numeric record](FeatureOutputAtomOwnership2026.json) supplies every complete function extent, chained unwind fragment and original-byte hash, selected instruction range, import identity, concrete RTTI and vtable cell. The [source receipt](../measurements/2026/FeatureOutputAtomOwnershipSource01.json) records the successful static replay. No vendor listing or binary is included.

## Serialization and object ownership

The actual concrete `moExtrusion_c` vtable `0x4cf3d488+0x28` selects `[0x4bb11640,0x4bb11888)`. It calls `moBodyFeature_c` at `0x4bb116c2`; the body-feature serializer calls the actual atom-feature serializer `[0x4bb0b0c0,0x4bb0cd82)` at `0x4bb0d46e`.

After the inherited and earlier embedded fields, the selected current context serializes the following distinct owners in order:

| Field | Wire ownership | Actual runtime meaning |
| --- | --- | --- |
| `has_f528`, optional `f528` | Signed 32-bit presence, then shared custom object-array serialization | Nullable array of actual created atom objects |
| `has_f530`, optional `f530` | Same framing | Nullable array of actual consumed atom objects |
| `f538` | Actual typed `moAtom_c` object-pointer grammar | Modified single atom, with output precedence |
| `n494`, `f498` | Signed 32-bit count, then signed 32-bit atom IDs | Retained ID slots, separate from live output-object membership |
| `f540` | Signed 32-bit scalar after that ID array | Separate atom-feature state, not an output count |

The pointer trio is reached at version `>=0x488` under its computed context gate; conditions `0` makes that gate true. Current ID-array loading requires version `>=0x491`. Context bit `1`, or bit `0x2000` at version `>=0x10bb`, excludes the ID array. These alternate contexts and legacy versions are not admitted by this note.

The actual `suObArray::serializePtr` `[0x3c8cfda0,0x3c8cfe5c)` stores canonical presence `0` for null and `1` for nonnull. Loading treats nonzero as present and allocates an actual array. An absent array and an allocated empty array are distinct states. `suObArray::Serialize` tail-jumps the custom `swccu!su_CObArray::Serialize`, not its `CArchive` overload. The selected non-DB path uses the shared `WriteCount`/`ReadCount` and actual object-pointer operators for the array elements, preserving archive object-map aliases.

After loading `f498`, `[0x4bb0b57f,0x4bb0b81d)` checks existing `f528` elements, dynamically recognizes actual atoms, and appends positive created-atom IDs missing from `f498`. It does not create `f528` objects from the integer array. Nonzero helper `+0x874` separately reaches reset/rebind helpers; those act on existing objects and are excluded by this selected profile.

## Native fresh-output construction

The exported `setOneCreatedAtom` creates a one-body input array and calls `setMultipleCreatedAtoms` `[0x4b717470,0x4b717930)`.

For an actual manager, null created array, zero prior ID count and one nonnull actual body, the source performs this sequence:

1. Allocate and install the created array at actual feature `+0x528`.
2. Count nonnull input bodies into actual `+0x494` and allocate the signed ID slots at `+0x498`.
3. Call manager allocation `0x4bcf0ca0`. It increments actual manager `+0x260`, constructs an actual atom with that ID and manager, and inserts it in the manager's map and ordered tree.
4. Store that allocated atom's actual `+0x140` ID into `f498`, request raw atom state `0`, and set creator/base feature `+0x150` to the actual feature.
5. Call actual `moAtom_c::setBody` with the actual body and feature.
6. Append the same actual atom object to `f528`.

The preexisting-ID branch can reuse retained slots after a manager range check and actual lookup. The range helper at `0x4bcf9230` tests only `requestedID <= manager+0x260`; it is not a membership test. No fixed atom ID, fixed old-atom count, persistent-node allocation increment or kernel-process allocation delta follows from these functions.

Current atom storage obtains last-modifying and creator identities from actual feature pointers `+0x148` and `+0x150`; concrete feature slot `+0x188` reads actual `f08`. At current load, `f130` and `f12c` hold those signed identities instead of the older direct feature-pointer fields. The actual atom body starts null; `body_kind=0` does not publish a current solid body. Saved integer identities do not substitute for the actual output-array object alias.

## Ordinary reload and live lookup

`getNumberOfOutputAtoms` `[0x4b706160,0x4b706181)` returns `1` for nonnull `+0x538`; otherwise it returns the created array's actual signed count, or `0` for null `+0x528`. It never reads `f498`.

`getOutputAtoms` `[0x4b706600,0x4b70674e)` has the same modified/created priority and copies actual object identities. It has additional delegated fallback branches only when those owners are absent. The count getter does not implement those fallbacks.

In ordinary `moPart_c::replaceBody`:

- `0x4c1cf82d` follows the output-count call. Zero count invokes actual extrusion slot `+0x1cf8` and skips to `0x4c1cf8fb` when it returns true.
- The exact slot target `[0x4bad6d00,0x4bad6d30)` returns signed `getCreateVersion() >= 0xd7a`. That getter returns actual feature `+0x2b0`. A feature actually created at `19000` therefore takes the skip for zero output objects.
- The earlier implicit `setOneCreatedAtom` route is limited to its selected class/null-array/mode guards and actual creation version `<0x7d0`. It cannot be presumed for a freshly authored current-version extrusion.
- Positive output count supplies the first actual output object. In the selected mode-1 or multi-output branch, a positive actual body atom ID looks up the actual manager atom. That exact object must occur in the actual feature output array; an equal-looking separate node is insufficient.
- Only a selected atom and the remaining actual guards reach `0x4c1cfa1f`, where `setBody` can publish actual atom `+0x160` and last-modifying feature `+0x148`.

The numeric observation boundaries are `0x4c1cf82d` (count), `0x4c1cf8a4` (actual manager lookup), `0x4c1cf8da` (actual object index) and `0x4c1cfa1f` (selected publication call). The record gives exact register domains. Their instruction boundaries are verified; this is not a software-interception/relocation-safety claim.

## Existing SDK and verification boundary

The current SDK `Archive/Bodies/Layouts/Resolved/BodyFields.py` already separates `has_f528/f528`, `f538`, and `n494/f498`, and uses shared typed nodes and arrays. Its checked source fingerprint is in the numeric record. No SDK, schema, constructor or writer was changed here.

The original-PE metadata replay verified **3 modules, 33 complete functions, 36 decoded instruction windows, 7 data/RTTI ranges, 22 imports and 6 vtable cells**. This executed only independently authored metadata parsing and hashing. It did not execute vendor code, the SDK, a codec, tests, CAD, COM or a VM. No held-out payload was accessed, and no Hopper/REA target was opened.

The first unresolved discriminating fact is the count and exact output-object membership in the same actual cold-open invocation. A source-backed reason for a modern zero-output skip is now closed. Whether that branch explains the particular native failure, and whether a complete neutral output graph restores usable initial bodies, remain root-owned measurements. Public and held-out writer qualification are unchanged.

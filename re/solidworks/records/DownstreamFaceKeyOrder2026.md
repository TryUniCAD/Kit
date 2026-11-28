# Ordinary downstream face-key construction and insertion, SOLIDWORKS 2026

The pinned source defines ordinary prism key text and its original and alternate lookup order. Generated cache qualification remains open. [Evidence vocabulary](../../Playbook/Evidence.md)

Task `B04-SW2026-DOWNSTREAM-FACE-KEY-ORDER`, owner `configuration_header`, delivery PR #121. Root owns generated construction, SDK integration and native qualification. This source tranche provides a replayable collision predicate. [Stored face source](DownstreamStoredFaceState2026.md)

The replay verifies 26 complete functions, 64 source intervals, seven virtual slots, three runtime descriptors and six typed imports in the originals below. [Numeric ledger](DownstreamFaceKeyOrder2026.json) · [Source receipt](../measurements/2026/DownstreamFaceKeySource01.json)

| Original | SHA256 |
| --- | --- |
| `sldmodu.dll`, preferred base `0x4b140000`, 46,536,280 bytes | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldutu.dll`, preferred base `0x3cf80000`, 4,061,272 bytes | `dbc147c10b658544e44a7c13d3ae656c26a0778e9241fe74d6ca9ecae8730933` |

## Exact selected key text

The selected route is an ordinary part with one rectangular-prism boss, local cap and sketch-entity surface representations, `BEnt.fe8` flag 4 clear and the default numeric text profile. It traverses the actual inline surface order.

Wrapper `0x4b526a60` calls `0x4b5297d0` with zero for the pointer-metadata option and the optional identity-word suffix. The part table's `0x4d1252d8 +0x1a8` slot returns false and the selected text starts without a body index. [Part-table binding](DownstreamIdentityMembership2026.md)

1. Start with ASCII `s,`. Native flag4 selects `S,` instead, outside the selected fresh profile.
2. Visit every inline ID in actual order, including own index0. Skip null representation pointers and empty extraction results.
3. For each actual cap or side, derive its signed-i32 integer sequence below, convert each integer to decimal and join with literal commas, without a leading or trailing comma.
4. Append those representation strings directly, with zero bytes between them.
5. Hash the exact `std::string` byte length. Reserved capacity and the terminating NUL are outside that length.

| Actual representation | Integer data from its concrete `+0xd0` |
| --- | --- |
| `moEndFaceSurfIdRep_c`, target `0x4c6c78a0` | `40`, actual `moFR.f10` feature ID, low32 of `moFR.f18` creation time, `moFR.f20 & ~0x10`, representation `f38` cap selector, representation `f3c` contour |
| `moFromSktEntSurfIdRep_c`, target `0x4c6c8030` | `74`, actual `moFR.f10` feature ID, low32 of `moFR.f18` creation time, `moFR.f20 & ~0x10`, representation `f38` permanent sketch-entity marker |

The actual FR is at representation `+0x20`. A negative cap contour normalizes to `-1` and other values stay as stored. The helper table at `0x4cdcb328` dispatches to the representation's concrete `+0xd0`.

The integer text helper `0x4b529fa0` calls the typed `basic_ostream<char>::operator<<(int)`. Array helper `0x4b52a3f0` preserves nonnull input order. Appender `0x4b5258d0` copies the described bytes and adds a terminating NUL. A cap ending `...,0,0` followed by a side starting `74,...` produces the text `...,0,074,...`.

The selected option-0 text contains ASCII digits, optional minus signs, commas and `s`. Other options carry metadata or assembly and body prefixes. Their scope includes separate flag, class and locale branches.

## Exact string hash

The imported `ut_hashStdString1` reaches `sldutu.dll +0x21120`, VA `0x3cfa1120`. It supplies base `0x8003` (32771) to complete helper `0x3cf9fd00`. For the selected ASCII string:

- Modulus `M = 1000000009` (`0x3b9aca09`)
- Initial accumulator `h = 0` and power `p = 1`
- For each byte in input order, `h = (h + byte*p) mod M`, then `p = (p*32771) mod M`
- Empty text or a text-construction failure returns zero

The native operation sign-extends `char` and truncates it to u16. The selected text is ASCII. Map traversal compares the 32-bit result as an integer. It uses a separate FNV-1a-64 hash of that integer's four bytes for bucket placement.

## Append row, search keys, then insert original

Creator `0x4b52b130` appends the wrapper and allocated ID to `f48` and the actual face table, then calls validator `0x4b5254f0`. The semantic key enters its own map only after both searches, so the current row has no key to find during validation.

The validator operates on the map at downstream `+0x7a8`:

| Stage | Exact rule |
| --- | --- |
| Original key | Compute from the actual reference. Zero returns false to the caller's fallback construction. |
| Original search | Bucket traversal compares the stored u32 key exactly at `0x4b525632/0x4b525644`. A hit enters `0x4b536bc0`. |
| Optional part-map shortcut | An actual part-map success can accept before the alternate lookup. |
| Alternate reference | `0x4b757970` creates a fresh FaceRef with the same inline count and swaps only indexes1 and2. It retains primary index0 and every other index, including separators. |
| Alternate search | Hash that clone. Zero skips the lookup. A nonzero key is searched against the same prior-key map at `0x4b5257aa/0x4b5257b8`. |
| Insertion | The ordinary no-hit path inserts **only the original key** at `0x4b525820`, with current row ordinal and actual face. Return1 keeps the selected original wrapper. |

A sufficient no-collision construction guard, with a fresh empty prior-key map and actual native traversal, is:

`original != 0 and original not in prior_originals and (alternate == 0 or alternate not in prior_originals)`

After both checks, add `original` to `prior_originals`. The selected path allows an alternate key of zero. The collision-repair and special-map branches require their own predicates.

## Deep equality and collision handling

Actual FaceRef `+0xa0` reaches `0x4b749bb0`. It first requires equal runtime class and count. The `gc_IsKernelParasolid(2)!=0` branch compares positional entity IDs including primary slot 0 and bypasses slots where both pointers are null. The other kernel has a separate cyclic-loop comparison.

Nonnull identical representation pointers compare equal. Distinct pointers invoke real representation equality `0x4b2dce80`: actual runtime class, actual keeper/FR semantics and subtype `+0x290`. For these two classes:

- Different cap/side runtime classes compare unequal
- Same-kind side suffix equality at `0x4ba87d80` compares the permanent marker `f38`
- Same-kind cap suffix `0x4c6cf060` compares `f38` and compares `f3c` when both contours are nonnegative

The keeper path `0x4bb5d3b0` calls `moFR::isSame` at `0x4bb35f50`, which compares file and feature-reference data. Equal ordinary ordinal `f64=0` yields success after the ID comparisons. Other ordinal and count combinations have separate paths.

Two caps with different selectors and four sides with different markers have distinct primary semantic owners. Compare both generated integer keys against the earlier originals to establish the no-hit branch. A key hit can cause `0x4b536bc0` to reconstruct the earlier component even when deep comparison finds different references.

## Verification and remaining limits

Run the verification tool with the licensed original `--bin-directory`, this `--record` and an unused `--output`. It verifies source identity, complete intervals and dispatch cells. [Replay tool](../../tooling/sw2026/downstream/VerifyFaceKeySources.py)

The generated prism replay applies this predicate to two in-memory part graphs. Native load, rebuild, edit, save and reopen remain qualification steps. [Generated proof](DownstreamPrismFaceStore2026.md) · [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [RE playbook](../../Playbook/README.md)

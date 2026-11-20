# Inactive secondary depth on a mid-plane through-all stock boss

The locked H01 SDK packet 02 passed the generated native lifecycle in four fresh processes, then failed its original-source comparison. A separate guest-side path audit identified only `stock.depth_reverse_m` across six observations. The cut definition had no differences. The original comparison and result remain the authority for that failure. This calibration uses disclosed inputs and carries zero held-out credit.

## Exact owner

`ThroughAllAuthor.definition` records `IExtrudeFeatureData2.GetDepth(False)` separately from the owned dimensions. The native source author calls `FeatureExtrusion3` with `Sd=True`, `T1=6`, `T2=0`, actual total depth D1, and the unused second input `0`. The visible stock has one editable D1. The signed body uses the total D1 divided about the sketch plane. [Author and observer](../../tooling/sw2026/ThroughAllAuthor.py)

The stock's `moExtrusion_c.f818` owns a schema-one `moEndSpec_c`. Fields `(f08, f0c, f10, f8c)=(1,6,0,0)` select ordinary forward mid-plane and leave the second direction inactive. The native `getDistance(index)` at `[0x4badf660,0x4badf691)` selects `f18` or `f20`, follows its handle and returns the value, or returns zero for a null display. Native command cleanup can destroy and null a disabled second display under the measured environment predicate. The shared geometry bridge reads both raw distance values before passing single-end and type fields. These facts do not make a retained second display a live driver. [Exact-build getter](EndConditionConstruction2026.md) · [Native prune branches](ThroughAllConstruction2026.md)

The SDK composes `BossEndInput(DepthValue, False, 19000, "mid_plane")` without `SecondDepth`. `MakeBlindMut` allocates a distinct D2 display and handle, `SelectEndValue` uses the primary value to initialize that inactive slot, and `MakeEndSpec` stores the object at `f20`. Its typed value lives at `moDisplayDistanceDim_c.f850[0].o → moFeatureDimHandle_c.ff0 → ParallelPlaneDistanceDim_c.f28 → moLengthParameter_c.f58`. `ReadExtrude` binds that slot as an active neutral dimension only for two lengths. For mid-plane stock the independent editable owner is D1 at `f18`. [Stock composition](../../../src/convert/adapters/solidworks/Archive/Construction/Part/FinishBlindMut.py) · [Display allocation](../../../src/convert/adapters/solidworks/Archive/Construction/Extrusion/MakeBlindMut.py) · [Initializer](../../../src/convert/adapters/solidworks/Archive/Construction/Blind/SelectEndValue.py) · [Typed owner](../../../src/convert/adapters/solidworks/Core/TypedResolved/ReadDepthOwner.py) · [End projection](../../../src/convert/adapters/solidworks/Core/TypedResolved/ReadExtrude.py)

## Independent disclosed observations

The three disclosed through-all sources use `end_forward=6`, `end_reverse=0`, `both_directions=false`, and one editable D1 in the author, initial reopen and rebuilt snapshots. Their source and edited states retain COM reverse depth `0` m. The independently linked D01 audit has literal null `f20` in each stock end. In the earlier passing generated G01 lifecycle, D1 and the inactive slot both read `0.03173` m before and after initial rebuild. After the D1 edit, D1 reads `0.04739` m and the inactive slot still reads `0.03173` m during save and fresh reopen. The whole tree, native stock edit and 72 geometry and ownership checks passed between healthy disclosed controls. [D01 typed read](../measurements/2026/ThroughAllD01ReadProcess01.json) · [Generated native result](../measurements/2026/SdkThroughAllSelectedBodyNative01.json)

| Disclosed lifecycle | Actual D1 before and after, m | Actual COM reverse depth before and after, m |
| --- | --- | --- |
| Native D01 source | `0.02791 → 0.04153` | `0 → 0` |
| Native D02 source | `0.03247 → 0.04637` | `0 → 0` |
| Native D03 source | `0.02483 → 0.03871` | `0 → 0` |
| Generated G01 | `0.03173 → 0.04739` | `0.03173 → 0.03173` |

The generated G01 observer's edit/save receipt has SHA-256 `2c491f91223addb5b3d8c10942e0b9195118f84cc7c885d6e9c74804212caba2`. Its fresh-reopen receipt has SHA-256 `13985f1742c9a88e7ad2ac63227fd20a7fe3ea76ba93c441c566e76879bb99f2`. The retained stale value establishes an inactive initialized display in this measured mode. It persists through an ordinary D1 edit and SaveAs. The existing evidence does not establish that a fresh generated part can omit the object or that changing to another end mode would preserve behavior.

## Matched disclosed calibration

The [calibration tool](../../tooling/sw2026/throughsource/CalibrateStockSecondary01.py) uses the accepted G01 scalar neutral intent, prediction and observer on SDK `6803987defeb0e69e39542b05eaa3618aefb46ff`. Two fresh isolated workers independently generate both complete selected-stock candidates with the same exact encoded locator. `Present` must match the unmodified SDK constructor byte for byte. `Absent` detaches the one verified inactive display from the fresh typed graph and re-emits every stream through `FinishScopePart`. The direct linked read checks active D1, depthless cut and real selected-stock atom and wrapper on both arms. The traversal compares all reachable Config/Resolved classes, field values and aliases, with exactly one differing edge. Inputs contain no source archive or stored field program. All ten streams independently replay byte-identically for each emitted archive.

The first host precursor, `MidPlaneStockSecondary01`, had freeze SHA-256 `c54813d07ee62af63ed7c62799eb1ffe5d1bd60d42449671db4d5f9c83103791` and `BuildProof.json` SHA-256 `a7d0777a1d5f6ab8cc6cf0829754a1f75fbcfed0de28006198f87a52a9d2a253`. Its independent runs reproduced both complete artifacts with zero audited external accesses. Only `Contents/Config-0-ResolvedFeatures` changed, `15,769 → 14,188` bytes. Config's next map slot stays `89`; Resolved moves `225 → 219`. The six unreachable objects are one each of `moDisplayDistanceDim_c`, `moFeatureDimHandle_c`, `moFavoriteHandle_c`, `ParallelPlaneDistanceDim_c`, `moLengthParameter_c` and `moNodeName_c`.

| Arm | CFB bytes | Exact artifact SHA-256 | Unchanged SDK cold read |
| --- | ---: | --- | --- |
| Present | 8,555 | `46c5aab4224ad881a4bdc5d06c433c4a8867c2cdeed9be17e85b123089c9e287` | Accepted |
| Absent | 8,475 | `7e4684998f91c24c137c1dca323312c0de2bd7206d2cd37e61deee13bf4c3486` | Refused |

The `Absent` probe establishes a separate SDK prerequisite. `ReadCutBodyLink` first succeeds at the actual stock wrapper, then delegates to `CheckColdPocket` and `CheckPrismEnd`. The latter requires four concrete display graphs unconditionally. The null `f20` therefore raises `typed model expected concrete schema one moDisplayDistanceDim_c` and the ordinary strict reader subsequently reports `SLDPRT contains no readable Parasolid payload`. No check was changed or disabled. [Selected scope route](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/ReadCutBodyLink.py) · [Cold part preconditions](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/CheckColdPocket.py) · [Display guard](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/CheckPrismEnd.py)

## Native discriminator and next boundary

One exact D01 source control brackets each end of the two-arm run. Both contain the disclosed source-like null secondary display. The two arms run serially with the same cold and saved C: locators. The common `InspectSelectedThroughAll.phase` handles zero-warning open, rebuild, all 27 actual recursive rows, four stock relations, real D1 edit, independent frozen analytic geometry, owned save and fresh reopen. The only staged candidate files are independently generated from neutral intent. Each arm moves its own immutable result into a separate receipt directory after its fresh reopen, so both arms measure the same live pathname. The calibration comparer expects all six baseline reverse queries to equal the initial D1 and all six absent-arm queries to be exactly zero. It compares every other stock, cut, profile and tree field and checks volume, area, COM and actual COM mass. The result preserves both raw depth series. Six distinct native processes are required.

`MidPlaneStockSecondary02` freezes the native observer wrapper and both complete disclosed arms. Manifest SHA-256 is `61365d7aee925dcf5b75e6bb5b8e342bdc0a58d69be7a888e6745acf22a79c9e`. `BuildProof.json` SHA-256 is `131a72025a4973626d09bc0db1edbcce80c1bcb1d7a42178520e801ed8a0307a`. All 19 manifest members were independently rehashed. The physical variant locators differ from precursor 01 by the packet number. The two graph proofs reproduce the same owner removal, length delta, counters and exact SDK cold-read refusal. Packet 02 adds no new native result at freeze.

| Packet 02 arm | CFB bytes | SHA-256 |
| --- | ---: | --- |
| Present | 8,553 | `192edf69f6afc1a8af42f2b28d223b57f361e5e0bfe917c331f2291ef21dba06` |
| Absent | 8,473 | `bd78d1014ae4727d403de409cd71ef6b23a3949081e85f2abdea3dbf9715fb94` |

The sole oracle owner can execute this disclosed calibration with the established Python 3.12 user-site COM environment.

```sh
guest='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\MidPlaneStockSecondary02'
prlctl exec 'Windows 11' --current-user py -3.12 -B \
  "$guest\Tools\CalibrateStockSecondary01.py" observe "$guest\Freeze.json" \
  61365d7aee925dcf5b75e6bb5b8e342bdc0a58d69be7a888e6745acf22a79c9e
```

`C:\KitSdkCandidates\MidPlaneStockSecondary02\Result.json` binds the two controls and four arm receipts. The approved source-like control remains at the exact previously accepted UNC locator. Both emitted arms are loaded from `C:\KitSdkCandidates\MidPlaneStockSecondary02\GeneratedInput\StockSecondaryCalibration.SLDPRT`. Their owned saves reopen at the same `Inspection\Generated\Saved.SLDPRT` under that private root before archival in the per-arm receipt directories. Native observations apply to this calibration and leave the existing strict SDK refusal unchanged.

If the disclosed native discriminator passes, use a narrowly selected explicit-null branch for the verified forward mid-plane stock and actual selected through-all consumer. Preserve all existing checks for the live primary display, two inactive draft displays, three independent dimension and parameter identities, positive D1, zero draft and exact other fields. Present secondary displays must still pass the original four-display checks. Keep ordinary prism, blind pocket, circle, two-direction and unproven modes on their existing contracts. Then verify the `Absent` derivative's typed `f20` ownership and actual saved selected-stock aliases, run the ordinary strict cold read on the fresh candidate with all other guards, and preserve the original H01 mismatch. An unused held-out slot can only be evaluated after a new pre-comparison freeze.

# Selected through-all stock secondary display in the SDK

The internal neutral through-all path now emits the explicit null `StockBoss.f818.f20` measured in the disclosed mid-plane stock calibration. It retains the authored total D1, independently allocated draft controls, selected-stock ownership and depthless cut. The exact ordinary SDK output was compared with the native-tested absent-display candidate. The original failed H01 comparison and source-equivalence refusal remain separate evidence. [Display calibration](ThroughAllStockSecondary2026.md) · [Six native phases](../measurements/2026/MidPlaneStockSecondaryNative01.json)

## Shared construction and read boundary

- `MakeScopedThru` validates the actual sole selected stock and attaches its body wrapper to the same freshly constructed boss and cut. It checks the forward mid-plane end and the four expected display owners on that actual boss, then clears only the archive edge to the inactive reverse display. The shared stream and container writers recompute linked map slots from the resulting graph. The all-body builder still uses the existing four-display graph. [Selected construction](../../../src/convert/adapters/solidworks/Archive/Construction/ThroughAll/MakeScopedThru.py)
- The normal history reader qualifies the actual selected atom and wrapper before the cold cut checks. Those checks opt into the explicit-null branch only for the selected through-all stock. The normal cold B-rep reconstruction propagates the same verified selected-stock role from `ReadPocketGeom` into `ReadPrismPlan`; this separately reaches the end gate a second time. [Stock owner link](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/ReadCutBodyLink.py) · [History checks](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/CheckColdPocket.py) · [Geometry input](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/ReadPocketGeom.py) · [Prism plan](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/ReadPrismPlan.py)
- The alternate wire shape requires an actual `f20` key with a null value, the forward mid-plane stock mode, and no active second owner or end. It preserves the same nonoffset start, absent reference collections, zero draft flags and values, and actual independent primary and draft identities. It verifies the live D1 display, dimension and parameter, plus three distinct nonnegative native dimension identities. Present secondary displays still take the original four-display route and must equal the primary initialization. [Cold end guard](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/CheckPrismEnd.py)

## Guarded process evidence

The [verifier](../../tooling/sw2026/throughsource/VerifyStockSecondarySdk01.py) used the public disclosed `MidPlaneStockSecondary02` freeze `61365d7aee925dcf5b75e6bb5b8e342bdc0a58d69be7a888e6745acf22a79c9e` and the exact sanitized native result `a77fd9262fb9d92e31cdfa18778c3a9d7dd7e8543802795956ead2a6a8d65892`. It copied the current SDK closure from the aggregate based on `cb78cb757cc142930125639810991def7d5d8255` into isolated scratch storage and hash-pinned the four changed files. The comparison closure replaces only those four files with their exact pre-change bytes, which also match the immutable disclosed SDK archive. It compares complete containers and all ten typed streams, reads both actual body owners, and checks normal strict B-rep reconstruction. After imports, the workers guard file opens, enumeration, subprocess, socket, registry and native-module access. The writer receives a portable document without a saved archive or recorded program.

| Comparison | Observed result |
| --- | --- |
| Normal `PrepareThroughPart` at the exact disclosed C: locator | Current selected output `bd78d1014ae4727d403de409cd71ef6b23a3949081e85f2abdea3dbf9715fb94`, 8,473 bytes, an exact byte match to native-tested `Absent` |
| Same verified old path | Exact byte match to native-tested `Present` `192edf69f6afc1a8af42f2b28d223b57f361e5e0bfe917c331f2291ef21dba06`, 8,553 bytes. The current normal reader still reads its same solid |
| Front forward, Top reverse and Right two-direction cut | All three all-body outputs unchanged. All three selected outputs construct and strictly read the same roles, with a change confined to `Contents/Config-0-ResolvedFeatures` |
| Active and draft roles | The same actual dimensional identities, stock atom and consuming cut. The stock remains forward symmetric. Both cut modes still have no driving length |
| Exact Front cold solid | 1 closed body, 8 faces, 14 edges, 10 vertices. Volume `0.00014698231687812168 m³`, area `0.01897372009982562 m²`, COM `(0.0014804889430259423,-0.0022446324958918496,-0.00013674580138999838) m`; independently predicted values agree |
| Process boundary | Three fresh guarded workers, two identical current results, and zero audited external accesses |

The malformed stock wrapper, active second end, reversed stock, missing primary display, missing secondary field, independent initialized secondary length, missing or nonzero draft, duplicate or unassigned draft dimension ID, and explicit null on the all-body route all refuse. Eleven actual linked-owner negatives are recorded. Ten can be re-emitted as archive inputs and also fail the ordinary strict read. The missing-key negative exercises the actual linked owner before serialization because a null on the wire has its own typed representation.

The [process receipt](../measurements/2026/SdkSelectedStockSecondaryProcess01.json) has SHA-256 `1b093c310a6563f8cde552bf6576b608d710d4ef9546147b1cf98ef45f704a49`. Its 5,026-file current source manifest is `62e66ab7bb40401d483b71c3dd8ab220c4692f34e49d63b847c75a00b3c079e3`. The four-file comparison overlay manifest is `1d354b3d66835271b755177ec26001ac7a33d9b6fcf5612df0450cac14d20521`.

```sh
report_dir=$(mktemp -d /tmp/KitStockSecondarySdkVerified.XXXXXXXX)
python3.14 -I -B re/tooling/sw2026/throughsource/VerifyStockSecondarySdk01.py \
  verify "$report_dir/Result.json"
```

This verifies an internal repair and the exact previously native-tested disclosed artifact. The additional Top and Right results are guarded SDK observations. The host verification starts no native process and carries zero held-out credit. Whole-source equivalence, continuous automatic feature scope and public writer registration remain unqualified.

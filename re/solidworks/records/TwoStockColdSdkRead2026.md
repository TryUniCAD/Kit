# Strict SDK read of the cache-free two-stock selected cut

This slice advances `B04-SW2026-EXTRUDE-THROUGHALL` in PR #121 from aggregate `6d4fa7929ad7426ae088b770c7794d794ab3e57c`. It combines the independently proven cold graph, neutral geometry and saved presentation rules in the normal SDK read path. The exact before-change SDK rejects the disclosed 8,574-byte generated archive because it has no readable Parasolid payload. [Cold owner proof](TwoStockColdOwnershipRead2026.md) · [Disclosed native lifecycle and analytic reconstruction](TwoStockColdOwnerGraph2026.md#disclosed-native-regeneration)

## Admission and geometry

The narrow route requires physical absence of cached geometry and a version-19000 part archive. It checks one ordinary active `Default` configuration and two independent blind creates. The stocks have exact signed canonical Front then Right datums, separate actual `D1` display, handle, dimension and parameter chains, rectangular four-line profiles and a positive gap between the original boxes. The effect of the cut comes from the one free circle on the selected stock's actual datum. The owner and placements must alias the same linked configuration and resolved object map.

| Owner | Read result |
| --- | --- |
| Two `fd88` atoms | Actual manager slots retain their ordered provisional IDs. Both alias the stock's `f528` and match the inherited map. |
| Cut `f548` | The real earlier feature and managed atom resolve the explicit historical selection. The wrapper has a true self component, no face reference and zero kernel words. |
| Saved-result fields | The initial cut excludes consumed/result collections, result IDs, chooser state and the resolved body map. Its evidence publishes the two actual provisional stock IDs. |
| Presentation | The same linked ownership admits the exact 23 ordinary roots and 23 distinct public rows. It verifies the public decoder's ordering. The cabinet and environment lists have no stored members and there are no direct configuration helpers. |
| Portable cut | Both earlier steps are `create` operations. The cut preserves its own profile dependency and the sole historical body selection. Its effective world direction is +Z for the Front stock or +X for the Right stock. The original reversal word remains in its native attributes. |

The cold path uses the shared prism builder for the untouched stock. For a circle strictly inside the selected stock, it uses the ordinary two-cap cylinder cut. For a circle centred outside one side, it computes the two side intersections, the inward arc and the removed segment's area and first moment. Both intersections must lie strictly within that side and the cut must clear the opposite wall. Tangencies, corner breaks and ambiguous overlaps refuse. The trim and cylinder builders produce closed analytic solids with two distinct design-body IDs. The resulting body IDs follow the actual untouched and cut-producing features. Volumes, areas, bounds and uniform-density centroids are computed in millimetres. [Cold owner decoder](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/Cold/ReadColdOwners.py) · [Shared analytic construction](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/Cold/BuildColdGeom.py) · [Prior geometric rules and proof](TwoStockColdGeometry2026.md)

The two reconstructed solids carry no native kernel-body claims. The saved branch continues to require realized atom and face owners joined to its active partition. Cached, malformed or unsupported inputs use the existing read policies. The new route requires B-rep inclusion and an ordinary read rather than raw payload extraction. B-rep-disabled reads retain their established compatibility shape. [Read routing](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/ReadPartShape.py) · [Scoped presentation](../../../src/convert/adapters/solidworks/Core/TypedResolved/Presentation/CheckColdRows.py)

## Reproduce the process measurement

Use the pinned baseline and disclosed packet. The baseline source archive and the current reader run in different Python processes. The proof also uses the exact disclosed `ThroughMultiStock03` save in the sibling packet and the tracked L1 native part. It starts independent neutral generation before reading either comparison save.

```sh
base='6d4fa7929ad7426ae088b770c7794d794ab3e57c'
scratch="$(mktemp -d /tmp/KitPublicColdRead.XXXXXXXX)"
git archive "$base" -- src | tar -xf - -C "$scratch"
python3.14 -I -B re/tooling/sw2026/throughsource/twostockgraph/ProvePublicColdStocks.py \
  --packet /path/to/GeneratedTwoStockGraph01 --sdk "$scratch/src"
```

| SDK input | Explicit selected stock | Untouched volume (mm³) | Cut result volume (mm³) | Cut face count |
| --- | --- | ---: | ---: | ---: |
| Disclosed native-tested generated archive | Front / 19 | 1,120 | 1,256.306035734 | 8 |
| Fresh unrelated stock edit, 10 to 29 mm | Front / 19 | 3,248 | 1,256.306035734 | 8 |
| Fresh independent Right-stock selection | Right / 22 | 900 | 1,334.849010288 | 8 |
| Fresh enclosed bore | Front / 19 | 1,120 | 1,577.203552628 | 7 |

Prior healthy native snapshots supply volume, area and centre comparisons for the first two cases. The cut result retains 868.169391592 mm² of area and centre (21, −8.886027482, 6) mm during the unrelated edit. The Right-stock and bore cases use independent analytic predictions. All four read results have two validated closed solids and 23 public rows. The existing name scanner still emits its informational notice for the implicit Lights and Cameras row; the typed presentation retains that row.

Nineteen guarded processes recorded zero external access attempts. Crossed atom identity, a coherent wrapper aimed at the wrong datum, an unexpected realized result and a physically present empty cache all retain the strict missing-payload refusal. The no-B-rep and raw options, the saved selected part, the native derivative and the ordinary L1 control match the baseline SDK results exactly. The native derivative retains its legacy result at this baseline. Repository steering passed the 40 changed Python paths. Scoped Mypy reports the same 14 inherited diagnostics on both sides. [Guarded process](../../tooling/sw2026/throughsource/twostockgraph/ProvePublicColdStocks.py) · [Numeric receipt](../measurements/2026/TwoStockColdSdkRead01.json)

Receipt SHA-256 is `3adeb0742ae622ac383bf6b7cd5c577cf9bb050731bbcbdcbdffd08b99304228`.

This is SDK readback for the admitted profile. Native qualification of additional inputs, held-out comparisons, general two-stock conversion and public writer admission have separate exits.

## Combined integration

The cache-free route and the regenerated saved-history route were applied together on aggregate `117eb1a0adbec9221184a4fdd732a20800609c97`. Twelve cold and compatibility phases repeated their recorded outputs. Ten saved phases repeated the four strict successes, five guarded field refusals and no-B-rep compatibility result. A separate strict inspection of the moving-stock native derivative confirmed that the typed owner and two persisted B-rep identities survive the combined SDK routing. Across all 23 guarded processes there were zero external read attempts. [Combined receipt](../measurements/2026/TwoStockCombinedSdkRead01.json) · [Reproduction command](../../tooling/sw2026/throughsource/twostockgraph/ProveCombinedStockSdk01.py)

Combined receipt SHA-256 is `cb5f9582bd5bd3fcb5a727c710afe86ec0b64f9d348f27faf09eed91ceda93f7`.

# Cold two-stock ownership from a linked part archive

This research slice advances `B04-SW2026-EXTRUDE-THROUGHALL` in PR #121
from aggregate `454513a85e38f0dd03faa1c4ea52d5cff275b052`.
[`read_cold_stock_owners`](../../tooling/sw2026/throughsource/twostockgraph/ReadColdStockOwners.py)
accepts an in-memory `SldprtArchive` and uses the existing version-19000
Config-0 and ResolvedFeatures link. The result exposes that actual
`NativeLink`, two independent stock `ExtrudeOwner` objects, the cut owner,
their three signed transforms, both provisional atoms, the selected index
and atom ID, and the actual selection wrapper. An existing `NativeLink`
can enter the graph-only `decode_cold_stock_owners` boundary.

## Measured ownership

| Wire owner | Checked relationship |
| --- | --- |
| Ordered feature roots | The existing stock root and operation readers require two separate blind producers followed by the reversed one-direction through cut. The second producer is mode-0 `moICE_c`. Each operation retains its own preceding profile. |
| `moPart_c.fd88` | The two actual ordered manager members alias the corresponding stock's `f528` object and the inherited archive map. Their keys are consecutive, their producer IDs appear in `f12c/f130`, and `f260` equals the later key. Both pass `CheckColdAtom` with provisional, implicit-name state. |
| Cut `f548` | The actual wrapper's `f108` identifies a unique earlier producer. `CheckCutWrapper` checks its atom keys, counted lineage and self component against this producer. The wrapper and component must also alias the live archive map. |
| Depth `f818.f18` | The display, local handle, dimension, length parameter and name object form one mapped chain per stock. Both parameter names are `D1`, both lengths are positive, and the two chains have distinct owners and dimension IDs. |
| Profile references | Two canonical signed Front and Right frames come from the actual datum and profile transform. The cut resolves its datum through its own reference and must share the selected stock's exact frame and datum object. |
| Unresolved cut | The result and consumed atom fields are absent, the cut has no result key or active depth, and the chooser fields remain absent. The wrapper has no face carrier and its two kernel words are zero. |

The decoder derives selection from the stored earlier producer and
validates geometry placement afterward. It needs neither predicted
selection nor a neutral document. The admitted state has two provisional
stock atoms and no persisted cut result, consumption or saved face
carrier. The native saved-state reader remains separate.
[Native regeneration evidence](TwoStockColdOwnerGraph2026.md#disclosed-native-regeneration)
· [Saved archive ownership](ThroughAllMultiStockArchive2026.md)
· [Driving-chain gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/Extrusion/StockDepthsUseActualEndSlot.md)

## Guarded byte-reader observations

| Input | Typed stock feature IDs and D1 depths | Selected feature / atom | Cut support |
| --- | --- | --- | --- |
| Disclosed 8,574-byte initial archive `6eca4bed…` | 19 / 12 mm, 22 / 10 mm | 19 / 101 | Front datum 14, +Z |
| Independent 8,660-byte second-selected contrast `f8c7869b…` | 19 / 8.75 mm, 22 / 11.25 mm | 22 / 102 | Right datum 16, +X |

The independently authored contrast varies the stock dimensions, tool,
names and selected producer. Two deterministic generation processes
finish before the disclosed archive is opened. Both positive archives
then enter fresh instances of the same stdin-only reader. It verifies
the actual linked owners and reproduces ModelHeader, CMgr, Config-0
and ResolvedFeatures exactly in memory.

Fifteen altered graph processes reject an out-of-role producer,
inconsistent atom ID, coherent wrapper retargeting to the wrong datum,
foreign self component, detached or reordered manager members,
wrong allocator, realized atom, shared or renamed depth, detached
depth display, consumed or result atom, saved carrier and shifted
profile transform. Nineteen fresh processes recorded zero external
access attempts. The disclosed file's hash stayed unchanged.
[Numeric and source receipt](../measurements/2026/TwoStockColdOwnershipRead01.json)

```sh
python3.14 -I -B re/tooling/sw2026/throughsource/twostockgraph/ProveColdStockOwners.py \
  --source /path/to/GeneratedTwoStockGraph01/GeneratedTwoStockGraph01.SLDPRT
```

The custody-bound probe examines internal linked stream ownership.
The [deterministic research CLI](../../../Documentation/Tasks/ResearchCommandLine.md)
remains the workflow for whole-document capture. This proof adds
zero native runs, held-out cases, FCStd conversions or public SDK
support. Reconstructing full read geometry from the returned owners,
the native-saved body map, and public admission still have independent
exits.

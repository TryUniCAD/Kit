# Completed BaseBody archives for generated bare cylinders

Task `B04-SW2026-IMPORTED-BODY`, owner `/root/release_path`, delivery PR #121. The [host builder](../../tooling/sw2026/imported_body_source/BuildLocalCylinderPart.py) composes two ordinary SOLIDWORKS 2026 part archives from the explicit [neutral cylinder inputs](GeneratedLocalCylinderKernel2026.md). The host exit is exact typed ownership and periodic geometry readback at both nominated logical destinations. The embedded native lifecycle is pending.

The earlier [native binary exchange](../measurements/2026/GeneratedLocalCylinderExchangeNative01.json) measured these exact two raw kernel payloads in SOLIDWORKS 34.5.2.0604. The raw receipt SHA-256 is `aa4af60b944359540e694859ee150cb0651e58bf06f776da8d82bc9b59013b11`. Both candidates passed 76 comparisons each with zero load and rebuild diagnostics, eight healthy controls and ten distinct processes. That measurement applies to raw kernel exchange.

## Archive ownership

The builder renders the cylinder's model-derived typed nodes into the existing local BODY role and uses the [local storage envelope](../../tooling/sw2026/imported_body_source/LocalBodyEnvelope.py) to derive the UTF-16 group key, record lengths and compression frame. The [shared part emitter](../../../src/convert/adapters/solidworks/Archive/Construction/Part/EmitPartArchive.py) builds the other streams. The [import binder](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/BindImportMut.py) allocates the same actual atom to the part manager and the feature output. The [completed update](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/FinishImportMut.py) and [creation log](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/LogImportMut.py) derive the configuration and header state. The input explicitly supplies the ordinary part datum scaffold, `Default` configuration, `Imported geometry` feature, authored ambient light and modeled save time. The signed cylinder axis belongs to the geometry. The default Front datum belongs to the ordinary part setup.

Both parts contain 12 streams. Independent readback binds the physical `moBaseBody_c` schema-one owner, feature 18, to atom 101 at object-map index 51. The local route stores `Imported geometry`, an empty source filename and zero segment-mesh IDs. The fresh atom displays mode 6 with tag zero. The separate [generated rollback](../../../src/convert/adapters/solidworks/Archive/Partition/ImportHistory/MakeImportHist.py) owns a body-free WORLD, activation mark 2, local attachment mark 3 and three retained empty history rows. Its 606-byte stream has SHA-256 `5f578dff6c4481ce61b1b4f1188ce9115b64031d71a30231cb3727faf8cf0c75`. The active configuration owns one body and update 103. Both headers retain update 103 and body stamp 102.

In the [two disclosed stock cylinders](ImportedBaseBody2026.md#analytic-topology-contrast), native save reports atom 101 at map index 58, feature 26, activation and selected marks 3 and 7, and an archive tag of 316 linked to a local `BODY_MATCH` attribute. The completed generated planar witness starts with atom tag zero and gains tag 264 and selected mark 5 after its native save. Its native-saved local body carries 21 attributes, with `BODY_MATCH` absent. These measured values describe distinct allocator and save states. The new parts use the fresh modeled events and bare 23-node kernel.

## Host evidence

Five linked streams replay byte for byte from their decoded typed owners. The packed LocalBodies kernel replays exactly through the independent typed codec. Its neutral research projection measures one solid, one shell, three faces, two full circles and two derived seam vertices. The [independent analytic volume, area, centroid and bounds](GeneratedLocalCylinderKernel2026.md#deterministic-host-evidence) match in both cases. A separately generated planar part at each identical logical destination reads as one closed solid through the strict package reader. All 11 other stream byte identities agree in each comparison. The only differing stream is `Config-0-FeatureBodies/LocalBodies`.

| Completed part under `C:\KitCylinderPart01\Candidates` | File bytes | SHA-256 | LocalBodies bytes | LocalBodies SHA-256 |
| --- | ---: | --- | ---: | --- |
| TranslatedZ.SLDPRT | 8995 | `ffb0d3f587387500ebd774c18272cfb5abff377b278ba42c54b63df9b4e4bda1` | 820 | `62590bc987b5c78a2f536cf0f9a8db136a6e5e24960777119479bf6a256e9af7` |
| ReverseY.SLDPRT | 8992 | `ff0054be16d0b08d888ea6299f209f59cdc286b894cdb48c0a83203b38b6272d` | 824 | `b33f8eb1cad6d36fd84b3e8df7e1ce49cb94871e02807360d3a06158b7494006` |

The existing strict metadata read returns the actual imported feature and active configuration. The SDK's raw intake selects the exact 1414-byte LocalBodies kernel, 307-byte active partition and 520-byte history in each case. The ordinary geometry decoder returns no model for those payloads. The public strict geometry read then reaches the planar local classifier and refuses with `SLDPRT local geometry rejected: local body has an unqualified node inventory`. The typed curved projection used in this host probe remains research-only. Separate in-memory controls refuse missing rollback history and a changed local group key with the precise owning diagnostics.

Two fresh processes at aggregate base `8cb3fa1d522029f7188804804a1de53a29cb1f8c` produced identical 13,938-byte stdout, SHA-256 `0eadab712f6e01deedb106716b27b675ca83788aecaec1fd39fbc998132218fc`. The builder SHA-256 is `e908fdc2f999ed43cf1da7b3b749dfb38ad39a21c2b4e0265ea23fed86e7aa96`. The optional artifact run wrote both file hashes above. The guard observed zero construction and verification reads after explicit module and codec initialization. The host record covers zero embedded native processes and zero held-out cases.

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/BuildLocalCylinderPart.py 'C:\KitCylinderPart01'
```

Pass `--artifacts "$UNUSED_EXTERNAL_DIRECTORY"` to create the two generated files exclusively. The argument above binds the logical guest location independently of the host artifact directory.

## Next native measurement

The oracle owner should freeze the exact generated part hashes, nominated locators, periodic metrics, pristine application seed and disclosed stock cylinder controls in a standalone job. Use fresh application and stock BaseBody measurements before and after the candidate batch. The two candidates each require one cold open, rebuild and save copy phase and one fresh read-only reopen and rebuild phase. Preserve the input files and carry the actual persistent import reference into reopen. Require zero load, rebuild and save diagnostics, one live `BaseBody`, its implicit body label, the actual ownership of all three faces, and the signed geometry and six bounds already proven through raw exchange. Keep the original planar measurement defaults in [the native part lifecycle](../../tooling/sw2026/imported_body_source/ObserveLocalImportedPart.py). The periodic checks can reuse [the native cylinder observer](../../tooling/sw2026/imported_body_source/ObserveCylinderExchange.py). Accept an embedded lifecycle only after both control brackets and all distinct processes pass.

# Completed BaseBody archives for generated bare cylinders

Task `B04-SW2026-IMPORTED-BODY`, owner `/root/release_path`, delivery PR #121. The [host builder](../../tooling/sw2026/imported_body_source/BuildLocalCylinderPart.py) composes two ordinary SOLIDWORKS 2026 part archives from the explicit [neutral cylinder inputs](GeneratedLocalCylinderKernel2026.md). The host exit is exact typed ownership and periodic geometry readback at both nominated logical destinations. Both disclosed embedded native lifecycles pass.

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

At the recorded host revision, the strict metadata read returns the actual imported feature and active configuration. The SDK's raw intake selects the exact 1414-byte LocalBodies kernel, 307-byte active partition and 520-byte history in each case. The ordinary geometry decoder returns no model for those payloads. The strict geometry read then reaches the planar local classifier and refuses with `SLDPRT local geometry rejected: local body has an unqualified node inventory`. The host probe uses a separate curved research projection. Separate in-memory controls refuse missing rollback history and a changed local group key with the precise owning diagnostics.

Two fresh processes at aggregate base `8cb3fa1d522029f7188804804a1de53a29cb1f8c` produced identical 13,938-byte stdout, SHA-256 `0eadab712f6e01deedb106716b27b675ca83788aecaec1fd39fbc998132218fc`. The builder SHA-256 is `e908fdc2f999ed43cf1da7b3b749dfb38ad39a21c2b4e0265ea23fed86e7aa96`. The optional artifact run wrote both file hashes above. The guard observed zero construction and verification reads after explicit module and codec initialization. The host record covers zero embedded native processes and zero held-out cases.

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/BuildLocalCylinderPart.py 'C:\KitCylinderPart01'
```

Pass `--artifacts "$UNUSED_EXTERNAL_DIRECTORY"` to create the two generated files exclusively. The argument above binds the logical guest location independently of the host artifact directory.

## Native lifecycle

The [packet preparer](../../tooling/sw2026/imported_body_source/PrepareCylinderPart.py)
freezes the exact candidate hashes, logical locators, periodic
metrics and separate application, generated planar and stock cylinder
controls. The [guest observer](../../tooling/sw2026/imported_body_source/ObserveLocalCylinderPart.py)
reuses the existing part lifecycle and the periodic shape comparator.
Each case opens at its encoded locator, rebuilds and saves to a fresh
copy. A distinct process reopens that copy read-only and verifies the
actual persistent reference, complete ordered feature tree, face
ownership, periodic geometry and signed extrema.

SOLIDWORKS 2026 SP05.2 `34.5.2.0604` passes all ten distinct processes.
Both parts open and save with zero diagnostics, retain feature 18 in
`Default` and preserve one solid, three faces, two circular edges and
zero native vertices. The four candidate phases pass 304 measurements.
All six controls pass. The saved copies and initial candidates retain
their recorded hashes. The tested receipts cover two disclosed
completed part archives. Held-out evaluation remains open.
[Native receipt](../measurements/2026/GeneratedLocalCylinderPartNative01.json)

## Strict SDK geometry

The scoped periodic parser admits both exact cold candidates through
the normal reader. It binds the managed atom, actual feature wire span,
active mark and typed predecessor before reconstructing a named solid.
Both produce the expected design body with three faces, two circular
edges and two neutral seam vertices. The independent proof reproduces
both generated archives, matches the native volume, area, centroid and
bounds, exercises two planar and four marked controls and checks eleven
refusals. It uses zero guarded runtime file reads.
[Strict geometry proof](../measurements/2026/SdkBareCylinderGeometry01.json)

## Normal SDK publication

The normal registry writes the separately authored oblique part to
`C:\KitPublicPeriodic01\Candidate\ObliqueCylinder.SLDPRT` with its
real clock and active `Inspection` configuration. The 9,039-byte
candidate SHA-256 is
`120d5ef09767aa1180bcfbf3c6818331594d53ab0a5091cebfb625080803361f`.
Four distinct SOLIDWORKS SP05.2 processes verify both bracketing controls
and 152 candidate checks. The candidate retains its actual feature 18,
persistent owner, ordered tree, one solid and three faces. It opens,
rebuilds, saves and freshly reopens with zero load or save diagnostics.
The candidate and its save-copy hashes are recorded separately.
[Public native receipt](../measurements/2026/SdkPublicPeriodicNative01.json)
[Guest staging and observer](../../tooling/sw2026/imported_body_source/ObservePublicCyl.py)

The original disclosed TranslatedZ reference replays byte for byte on
macOS Python 3.14.7. The same model, event and logical path on Windows
Python 3.12.7 produces 8,990 bytes. Eleven logical streams are identical.
Exactly 56 wire bytes change in `Contents/Config-0`, all belonging to
eight two-ULP differences in the Left, Right, Top and Bottom camera
diagonals. The typed reader locates each live `moView_c.f368.f08`
coefficient and accounts for all changed offsets. Geometry, feature and
configuration ownership, and the local Parasolid body stay identical
in this arithmetic comparison. The new normal Windows operation uses
its own locked file identity in the native phases.
[Arithmetic proof](../measurements/2026/SdkPeriodicRuntimeMath01.json)
[Reproducer](../../tooling/sw2026/imported_body_source/ProbePeriodicRuntime.py)
[Shared standard views rule](StandardViewsConstruction2026.md)

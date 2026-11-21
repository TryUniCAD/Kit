# Single-edge angle-distance chamfer archive and physical owners

Task `B04-SW2026-EDGE-CHAMFER`, PR #121. The disclosed native source lock passed eight distinct processes, both controls and 212 design checks on SP05.2 `34.5.2.0604`. This follow-up reads those four exact disclosed archives in six guarded host processes. It binds the shared opt-in typed model, driver edits and physical rollback. The independent pre-writer source lock remains in separate custody. [Disclosed source lock](../measurements/2026/EdgeChamferDisclosedSource01.json) · [Independent source lock](../measurements/2026/EdgeChamferPrivateSourceLock01.json) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Typed archive

The ordinary part context uses version 19000 with compressed-model, part and CMgr `f658` flags equal to one. `ReadNativeLink(..., ReadChamfers=True)` permits schema-1 `Chamfer_c` through the established body, edge-reference, keeper and dimension layouts. It reads actual Config-0 inheritance and ends at map 325 from the Config-0 frontier 110 in all four cases. The production graph replays exact Config-0 and exact ResolvedFeatures using the separate research serializer. There are no provisional or missing SDK schemas and all three binary64 display cells have typed length and value reports. The original ordinary read and store each still refuse `Chamfer_c`. Both existing prepared rectangle and circle controls produce their same exact linked streams with the opt-in supplied or omitted. [Wire authority](ChamferArchiveAuthority2026.md) · [Explicit context](../../../src/convert/adapters/solidworks/Archive/Resolved/UseChmfCtxMut.py) · [Chamfer fields](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/Chamfers/ChamferFields.py)

| Field | Measured ordinary owner | Qualification |
| --- | --- | --- |
| `f880.ff0` and `f888` | Single `moEdgeRef_c` object at slot 284, aliased by the keeper and the selected `moCompEdge_c` at slot 295 | Confirmed object identity and ordered stock-face reference chain |
| `f8a8` | Separate wrapper 314 and edge reference 316 with the same four ordered stock-face keys and its own surface and feature references | Confirmed closure and physical equivalence in the disclosed profile |
| `f880.f18` | Two result keepers, `moSurfaceIdRep_c` and `moFilletSurfIdRep_c`, rooted in the actual chamfer's creation event | Confirmed result-face owner, construction still open |
| `f810` | `moDisplayDistanceDim_c` → local `moFeatureDimHandle_c` → `ParallelPlaneDistanceDim_c` → `moLengthParameter_c` named D1 | Confirmed SI metres, persistent dimension 33, exact `f5b0.data` match |
| `f818` | `moDisplayAngularDim_c` → separate local handle → `AngleDim_c` → `moAngleParameter_c` named D2 | Confirmed SI radians, persistent dimension 34, exact `f5b0.data` match |
| `f890`, `f898` and optional feature slots | Two empty lists and no secondary display/face/vertex/edge selection on this measured branch | Scoped absence only |
| `f8c8`, edge `f70`, display witnesses | Counted dwords, a writable archive reference field and typed presentation owners | Wire types known. Values, neutrality and constructor derivation still open |

The IDs in this table are evidence from the four archives. They do not control admission or become writer input. `ReadChmfOwn` resolves these actual objects and checks the two independent driver vertices. The first pair is edited only in D1 from 0.004125 to 0.005625 m, keeping D2 at 0.5017821599483697 rad. The second pair keeps D1 at 0.003375 m and edits D2 from 0.619591884457987 to 1.069014166846527 rad. In each phase the relevant `f28.f58` and exact binary64 display cell agree. The implementation retains the two local driver chains and the distinct selected and extra edge references as internal archive owners. [Typed ownership reader](../../../src/convert/adapters/solidworks/Core/TypedResolved/Chamfers/ReadChmfOwn.py)

## Physical rollback and bevel ownership

The inherited atom has ID 101, creator 32 and last modifier 35. The current and restored body occupy the same transmit slot and retain their actual atom and body tag. The active implicit name belongs to the chamfer. The restored name and last modifier belong to the preceding stock. The original rollback walks mark IDs 13 → 11 → 3 → 1. The edited rollback walks 21 → 19 → 3 → 1. The selected undo explicitly revives the chosen stock edge as a typed record. The next undo deletes the stock. [Existing retained-body history grammar](EdgeFilletRollback2026.md)

| Disclosed archive | Resolved bytes | Stock edge transmit slot | Reference `f70` | Result face transmit slot | Selected undo restored / removed / copied / capacity |
| --- | ---: | ---: | ---: | ---: | --- |
| Axial A | 16,655 | 222 | 1,929 | 48 | 26 / 64 / 76 / 79 |
| Axial A edited | 16,825 | 221 | 1,505 | 46 | 26 / 63 / 76 / 79 |
| Transverse B | 16,647 | 227 | 1,839 | 48 | 29 / 67 / 78 / 81 |
| Transverse B edited | 16,797 | 226 | 1,418 | 46 | 29 / 66 / 78 / 81 |

Each of the two edge references resolves the same four stock faces by actual representation type, producer ID, creation event from both headers, configuration and ordinal. The configuration and locators bind to the actual local part. The first two faces own the same straight edge through the two opposite fins. The third and fourth are distinct endpoint-only faces. The axial order is side 2, side 1, end 1, end 0. The transverse order is end 1, side 3, side 2, side 4. Both ordered chains resolve the independent native selected endpoints. The restored edges carry no per-edge attributes. The positive stored `f70` values differ from the transmit indices and kernel node IDs. The second reference uses zero for `f70` while preserving the ordered face keys. [Selector identity gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/Topology/ChamferEdgeReferenceIsNotTransmitIndex.md)

The active typed partition replays byte-for-byte after converting its existing kind-84 ASCII byte values to the shared canonical text type. The result has seven planar faces, fifteen edges and ten vertices. Its sole chamfer face has `FACE_ID_2001` class word 72, the actual chamfer producer and creation event, and keeper ordinal 1. Its four vertices and the full solid agree with the independent clipped-prism analytic branch. The measured setback from the selected edge on the first incident face is `D1*tan(D2)`. On the second incident face it is `D1`. The two distinct edge directions and independent D1 and D2 edits preserve this ordering. A construction rule for initially choosing this order for an arbitrary edge has its own evidence gate.

## Scope and reproduction

Each original process refuses a changed mode, crossed keeper, foreign body atom, stale angle display, alternate compressed-model context, simultaneous finish profiles and a foreign stock creation event. The ordinary decoder and emitter continue to refuse the feature in all four source processes. The tool uses two guarded controls and four independent input workers. All six report zero file, process, network and library accesses inside the guarded read/replay. The checked-in result has SHA-256 `e408295c20bf3d5f0529de9217ea3aebb951fc1a91d827044940e83c4e10651c` and binds the implementation files individually. [Guarded proof receipt](../measurements/2026/EdgeChamferTypedArchiveRead01.json)

```sh
python3.12 -E -B re/tooling/sw2026/edge_chamfer_source/AuditTypedChamfer.py \
  --folder /absolute/path/to/disclosed/EdgeChamferSource04 \
  --report /absolute/unused/EdgeChamferTypedArchiveRead01.json
```

The supported result is a reusable internal typed archive read plus disclosed physical evidence. Public feature projection, a portable editable edge selector, model-derived keeper and display construction, open-cache neutrality of `f70` and `f8c8`, and cold native generation remain open. A useful next native discriminator would vary the component-reference cache separately from the ordered four surface keys on an independently generated, otherwise identical part with the same target, then require cold geometry and both driver edits. This tranche wrote no CAD output and accessed no protected sources.

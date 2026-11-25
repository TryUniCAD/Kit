# Saved cuboid Design height evidence

[DesignHeightEvidence.py](DesignHeightEvidence.py) checks associations in the four archives pinned by the [saved cuboid corpus manifest](../SavedCuboidRoundTrip/Corpus/Manifest.json). It verifies each archive against the manifest and the digest in its separately hashed native observation receipt before decoding. The copy of the manifest in the checkout is the trust root. The script runs the strict public projection for the positive XY fixed-corner cuboid and uses typed reference joins to measure its Design, ACT, Browser and geometry dependencies. It writes deterministic JSON to stdout and emits no CAD archive.

Run from the checkout root with Python 3.14 and the checkout SDK on the module path. The following PowerShell command uses the active Kit environment.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedCuboidWriter/DesignHeightEvidence.py
```

## Verified associations

| Fixture | Height literal | Stored centimetres | Analytic volume in cm³ |
| --- | ---: | ---: | ---: |
| Baseline control | 13.8 mm | `1.3800000000000001` | 6.133272 |
| Baseline edited | 28.3 mm | `2.83` | 12.577652 |
| Baseline restored | 13.8 mm | `1.3800000000000001` | 6.133272 |
| Independent holdout control | 31.4 mm | `3.14` | 17.701122 |

The extrusion distance identifies its model parameter, which resolves back to the same extrusion slot. The model expression names exactly one user driver in the owning component's parameter table. The user driver, model parameter and extent agree exactly in native centimetres and with multiplication of the parsed millimetre literal by `0.1`. In the holdout, division by `10` yields `3.1399999999999997`, one representable value below the stored `3.14`.

Each BRep history and typed snapshot agrees on the prism model and topology tags and passes the existing prism frame guard. The extrusion's start and end history references agree with the history. Independent cuboid formulae reproduce the body's area, volume, centroid and inertia cache with relative and absolute tolerances of `1e-12`. The separate [analytic frame prediction](../SavedCuboidRoundTrip/PrismFramePrediction.py) measures a frame update across captured heights.

Each fixture has 15 predecessor timestamps that equal the update time on their referenced owners. The BRep authoring time joins the extrusion update time. The ACT table references its asset snapshot revision and its Geometry domain revision. The body cache references the Geometry revision on its own ACT row. Those three revisions, the component's Design revision and the asset's physical change revision occupy five distinct roles. The Browser contains 100 references resolving to Design, one to ACT and 127 to Browser per archive.

The same-asset 28.3 mm to 13.8 mm pair changes 35 matched Design records and four matched ACT records. Browser records and segment metadata remain equal. Seven Design cache records are replaced, accounted for by the datum plane and its progenitor and recipe, two identity matrix caches and two component-scoped topology caches. The table and component change Appearance, Geometry, Properties and StructureChange. The body changes Appearance and Geometry. The sketch changes Geometry. The occurrence retains every revision. The two independent control files carry extra body domains PhysicalMaterial and Properties, so the script checks those controls and the edited pair against their own measured inventories.

## Verification and limits

Two fresh Python processes produced byte-identical UTF-8 reports with SHA-256 `8f030ab003863323d022a449f39c021ad3e8c5c676bcb9b6514f24230bd4a977`. Separate probes refused a wrong archive digest, a wrong receipt digest, an escaped corpus path, the holdout presented as an edited fixture and a self-pair. The report measures one pinned edit and restore pair with two independent controls. All observations come from previously captured archives.

Revision changes and allocation counts identify observed dependencies. A repeated unchanged export at each height is still needed to distinguish solve changes from ordinary export churn. Regenerating identifiers, timestamps, cached topology, graphics, texture mapping and auxiliary data remains unresolved. The [saved cuboid findings](../SavedCuboidRoundTrip/Findings.md) show that aggregate graphics bounds can carry the previous height and that child bounds have a different dependency. This check uses solved geometry for dimensions and leaves the original graphics data intact. The evidence establishes no edited writer or fresh native acceptance under the [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).

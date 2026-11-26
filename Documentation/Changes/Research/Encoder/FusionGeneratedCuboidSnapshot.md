# Independently generated Fusion cuboid snapshot

The research generator creates a new fixed-corner cuboid and its three-root snapshot from a persisted semantic request. It generates the reciprocal Design ownership links, snapshot member identity and physical geometry through Kit's existing authoring and snapshot codecs. The generator does not read a source archive.

## Use

Use the [source-free cuboid request schema](FusionSourceFreeCuboid.md#usage). Run the generator with Python 3.14 and the checkout SDK available from `src`. Choose a new `.f3d` output path.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/GeneratedSnapshot/GenerateSnapshot.py Request.json Candidate.f3d --written-at 1795564800
```

The receipt identifies the exact request, archive and snapshot member. It records the tool solid, profile region and sketch sheet IDs. Three zero address entries are emitted within this generator's experimental scope. The previous [saved archive measurements](../../../../re/Fusion/SavedCuboidSnapshot/SnapshotAddressContrast.md) observed native regeneration from zero values on two existing owner graphs.

## Verification

The new path uses the existing strict version-2 reader and its [snapshot ownership rules](FusionCuboidSnapshotOwnership.md). It writes the requested asset title to `documentName` and requires the strict neutral configuration title to match before publication.

Separate generated archives for the 15.9 mm baseline and 24.7 mm height edit passed strict SDK readback and persisted JSON equality. The public configuration retained the requested title. The sketch and extrusion names and complete feature timeline survived JSON reload. Both snapshot payloads were byte-identical to their pre-repair versions, and the earlier archive digests were verified separately.

| Case | Archive SHA-256 | Persisted JSON SHA-256 |
| --- | --- | --- |
| Baseline | `177c4fb5fb1a7e0e6b764b78108e04d2dab7c80cb5df126d4aadcd4722ae03df` | `6b1ec40113b29700144f3ba6b03646477fca241f98f8775dc7af11a4ecaa958a` |
| JSON height edit | `92061b2451a4eddafe212fc07afc67556e0dfc3d58e7604d3aae8eadf0f001c0` | `2ac1657103c3a843f9a862bcac37cfcb447bca20c5d83b29f262f744c7752c88` |
| Independent holdout | `aa85873d4e83388c15d8e62451f17459edaec85f51d46048496489d0304435ad` | `254467f5899cc93c8d7b57f283b116d55bd4220bc48a5637e0d97a54b107675c` |

The holdout request was set aside before the generator rules froze. A separate SDK run checked the exact embedded snapshot, ordered owner roles, feature and driver bindings, physical material and requested title. The generated snapshot member was 11,912 bytes with SHA-256 `d39cffac09e9bf783eaa63cc99dfce42af8dfbe14f4464903897f6c573bbb259`.

Two fresh-process integration cases passed in 24.94 seconds on Python 3.14.6. Each case started with only its written JSON request and verified the resulting title, feature timeline, height, volume and complete version-2 state. Both ordinary snapshot-free cuboid outputs also reproduced their existing exact digests after the packaging change.

A separate check ran three fresh CLI processes in 27.134 seconds. Each process started in a new directory containing only its request. Two independent processes produced byte-identical baseline archives. The baseline SHA-256 was `eace1303fba9de750d1b5f013bce28dcad5dbcce4f0638ea53cd1e3a552582a7`. Changing height from 18.875 to 26.5 mm produced `4f08598a5faa3f5d3a1bfa7acee7c5dda67de07b36dbca2ba10749d349200e65`. Strict SDK and JSON checks passed on all three. The existing snapshot-free version-1 constructor and four vendor-saved version-2 fixtures also passed their readback checks.

The title repair follows the [asset-title rule](../../../Gotchas/Conversion/Fusion/Geometry/Snapshots/FusionSnapshotAssetTitle.md). The [member path](../../../Gotchas/Conversion/Fusion/Geometry/Snapshots/FusionSnapshotMemberPrefix.md) and [parameter observer order](../../../Gotchas/Conversion/Fusion/Geometry/Snapshots/FusionSnapshotParameterObservers.md) describe two further boundaries exercised by this generator.

## Limits

The authored request has one supported cuboid and one generic physical material. The generator does not ingest a vendor-saved design. These generated snapshot-bearing archives still need direct native Fusion measurements. Full preservation of a saved source's graphics, previews, visibility, configuration, face selection and procedural material state remains open. Version-2 readback retains `fusion.read_only`.

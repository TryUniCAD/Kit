# Placed plate and seed in local linear pattern construction

Task `B04-SW2026-LOCAL-LINEAR-PATTERN/placed-stock` in PR #121, owner `/root`.
The shared plate and seed constructor keeps the authored lower X and Y on the Front plane.
Both extrusions start at their common Front datum and retain independent forward blind D1 owners.
The raised seed must extend above the plate and stay strictly inside its footprint.
The joined bounds use the plate's lower corner and lateral extents and the seed's upper Z.
[Construction receipt](../measurements/2026/LocalLinearPatternPlacedStock01.json)

The original SOLIDWORKS 2026 SP05.2 disclosures cover two separate translated plates and their actual raised seeds.
The observer binds both frozen author intents and all six original, count-edited and pitch-edited file hashes.
Their typed Config and ResolvedFeatures streams re-emit byte for byte.
The actual Front datum, four live corner owners and D1 agree with the pinned intent for both stocks in each file.
The retired point rows are excluded from the native geometry comparison.
[Disclosed archive and source custody](LocalLinearPatternDisclosedArchive2026.md)

Two stock graphs built from the recorded author intents retain their placed geometry, live D1 handles and actual managed atom chain.
Each model repeats in two guarded processes.
The five modeled streams re-emit exactly after linked readback.
Two further control models at the origin reproduce all ten prior stream hashes in four guarded processes.
No guarded build accesses source data at runtime or writes a CAD file.
Co-incident side, disjoint stock, insufficient depth and a displaced start remain typed refusals.

The public oblique writer still requires its original origin-plate profile.
A complete principal pattern and its own native validation remain open.
This result has no held-out or FCStd corpus credit.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePlacedPatternStock.py \
  --disclosed /absolute/path/to/LinearPatternSourcePacket03/DisclosedNative \
  --output /absolute/unused/PlacedStock.json
```

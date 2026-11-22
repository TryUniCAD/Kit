# Strict circular extrusion extents

## Behavior

The strict Fusion reader decodes untapered circular XY extrusions with negative distance, symmetric full or per-side distance, and distinct two-sided distances. The neutral `DistanceExtrude` retains the actual signed driving value, sidedness, second distance and second taper bindings. The geometry uses the evaluated lower and upper stations.

The reader validates the active typed journal, saved snapshot, body serializer, reciprocal operation indices, physical cap orientation, closed circular rims, source curve tags, and analytic mass cache. Symmetric side faces can contain two operation groups. Allocated but inactive operation IDs remain distinct from operations present on live geometry.

## Usage

Use `kit decode FILE.f3d --output OUTPUT.json`. No CAD runtime participates in decoding. The existing native API remains an independent measurement instrument.

## Evidence

`re/Fusion/Reconstruction/CircularSpans/Manifest.json` records original and held-out API-authored samples with measured bounds, volume and area. Both sets have healthy before/after controls. The original reversed, symmetric and two-sided cases decoded successfully through the public CLI. The held-out cases use changed positions, radii and depths. Thirteen recorded archives include both symmetric measurement conventions. All thirteen committed cases decoded strictly through the pinned research CLI with zero rejected inputs, reader errors or partial fallbacks. CLI integration coverage compares geometry measurements, complete timeline length and live extent parameter roles against the recorded native observations. Remote CI and review remain pending.

## Limits

This adds strict reading for the stated circular extent profile. The new span projections carry the read-only marker. This does not qualify arbitrary multi-feature histories, taper on both sides, arbitrary planes, conversion, or native output acceptance. The separate multi-feature decoding work remains unfinished.

See [recorded format findings](../../../../re/Fusion/Reconstruction/CircularSpans/Findings.md).

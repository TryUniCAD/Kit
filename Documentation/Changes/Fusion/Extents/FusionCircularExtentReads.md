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

## Review repairs

Physical feature labels must now cover the actual solid face and edge owners. A sketch sheet label cannot substitute for a missing cap label at the same station. The integration replay checks serialized snake case field names and compares each parameter role binding against independent native role observations, including the two equal valued taper controls. Type and steering checks passed without executing local tests. Underconstrained source sketches remain underconstrained; this addition is read only and does not establish qualified conversion or round trip acceptance.

## Floating point boundary and rejection replay

Station coverage now uses the same centimeter arithmetic as the physical label reader, preserving valid 15 mm along and 8 mm against extents. Three additional API-authored controls bracket this rounding case. A process boundary integration replay encodes an archive with its solid cap label moved to a coincident sketch sheet and requires the public CLI to refuse physical label coverage. This replay is committed for remote execution and has not been run locally.

The expanded pinned offline CLI run at `be17166ec6c8dd17243e02605efac4ea571563cd` decoded all 16 committed captures strictly with zero partial fallbacks, reader errors or rejections. Its receipt is retained in Validation.json. The rejection replay and its topology selector now occupy separate focused modules. The replay remains unexecuted locally, and strict source decoding does not establish native conversion acceptance.

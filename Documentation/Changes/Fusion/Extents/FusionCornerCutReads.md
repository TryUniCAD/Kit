# Fusion corner cut source decoding

Strict native Fusion decoding now supports a bounded modifying history containing a rectangular stock sketch and create extrusion followed by a rectangular tool sketch and full depth cut extrusion. The source is decoded without a CAD runtime or advisor. The result preserves both sketches, their support planes, all four ordered feature steps, separate live distance and taper parameters, the modifying operation and its explicit target body. The output remains read only and is not qualified for native writing or lossless conversion acceptance.

## Usage

Run `kit decode input.f3d --output document.json` with the current source CLI. The modifying feature uses the new `DistanceCut` definition, wrapping a live `DistanceExtrude` and explicit `TargetBodyIds`. `GetCutValues` checks the modifying operation and evaluates exact owned controls. The existing create extrusion contract is unchanged. Neutral serialization registers the new type explicitly.

The qualified profile requires two independently owned XY axis aligned rectangles, positive untapered single sided extents, one body and a rectangular tool that removes one stock corner through the entire stock depth. Partial pockets, joins, intersections, rotated profiles, tapered tools and arbitrary boolean histories continue to refuse explicitly. A new type does not imply that every writer supports it.

## Qualification

The reader checks complete creation order, feature states, scoped sketch and datum ownership, union coverage of all profile and parameter entities, reciprocal operation allocation, native target body and ASM recipe identity, serializer body identity and journal state continuity. It derives the remaining concave outline from decoded sketch geometry and evaluated distances. It matches every oriented native face, its winding and physical normal, line edges and coedge mates against generated stock and final boundaries. It verifies exact feature label ownership through sketch curve progenitors and active operation IDs. It also checks the independent cached stock and tool solids and all four profile or sketch sheets, plus final native volume, area and centroid caches.

No convex guard is removed. Low level planar traversal can explicitly read an open sketch sheet; every solid still follows the existing closed ownership and edge mate checks. Scoped rectangular qualification admits numerical axis roundoff of at most 1e-9 mm while preserving every original sketch coordinate.

## Evidence and limits

The originally reported CornerCut archive now produces a strict neutral document with four history steps, one eight face solid, eighteen edges, twelve vertices, volume 22000 mm³ and area 5000 mm². Independent held out and opposite corner captures also decode with their own native measurements. The partial depth pocket remains a refusal. See [the native corpus](../../../../re/Fusion/Reconstruction/BoundaryCuts/Findings.md) and its recorded measurements and hashes.

Public executable integration replays cover the requested archive and varied native controls, editable parameter roles, target body dependency, geometry and unsupported pocket refusal. These tests are committed for remote CI and were not run locally. Actual CLI decoding is the authorized workload; static checks are reported separately. Complete conversion acceptance, source round trip writing and native verification of generated output remain unfinished and are not claimed by strict source decoding.

The final pinned offline regression at `5d4b34af5c5f33ebbc360ec84e84acde3d1f5fcf` decoded 22 committed assets strictly with zero partial decodes, reader errors or rejections. The original three named inputs also exited 0 with empty diagnostics at their requested output paths. All four full depth corner variants decoded strictly; the separately exercised partial pocket exited 1 with the explicit unsupported depth message. The regression receipt is retained in `re/Fusion/Reconstruction/BoundaryCuts/StrictReaderRegression.json`. Static type and steering checks passed for 48 changed Python files, Ruff reported no undefined or unused imports in that scope, and the tracked path policy passed. These checks do not replace remote integration or native acceptance.

Repeated public CLI decoding of the three exact requested inputs produced byte identical neutral JSON on the local runtime. Input and output SHA-256 values, source revision and source/CLI tree identities are retained in `re/Fusion/Reconstruction/BoundaryCuts/Determinism.json`. This repeatability evidence does not establish cross-platform or native output acceptance.

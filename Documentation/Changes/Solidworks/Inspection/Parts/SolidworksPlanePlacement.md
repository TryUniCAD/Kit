<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Principal-plane placement across native timestamps

The SOLIDWORKS reader now retains the selected principal sketch plane when the native reference timestamp changes.
Previously, a captured timestamp was treated as a format signature.
The resulting fallback placed 96 recovered top-plane and right-plane parts on the front plane.

The bounded reference reader consumes the unsigned timestamp without comparing its value with a captured constant.
It checks supported component generations, principal identity, axis agreement, null framing, finite orthonormal axes, and the complete local pose.
The origin reference supplies the source document's local unit and part identities.
The decode state caches that lookup, including an unavailable result, for the current immutable source stream.
Each candidate must retain those owners, the same generation, compact pointer kinds, and the absent external component.
The complete owner envelope stays inside its authored feature.
The pose must retain its principal origin, unit scale, and absent nested transform within the owning feature boundary.
All three saved axes must match the canonical native basis for the principal datum.
The neutral sketch references the datum frame. The reader rejects an in-plane rotation that this reference cannot represent.
This rejection applies to owned sketch references. The origin owner lookup retains its existing unavailable-owner fallback.
See [origin owner lookup and sketch pose validation](../../../../Gotchas/Conversion/Solidworks/Readers/OriginOwnerPoseFallback.md).
A compact reference with matching local owners and a principal identity raises a format error if its pose is invalid.
Unrecognized ownership or non-principal identities retain the existing fallback path.
Both supported generation stamps participate in fallback scanning.
The historical timestamp export remains available for compatibility callers.

## Verification

The existing native captures and their measured ground truth supply the comparison inputs.
No native files or historical reports were changed.

- All 144 ladder files passed full and design-only public SDK reads: 288 comparisons with zero centroid mismatches.
- Decoded cuboid extents agree with the source recipes and measured native centroids.
- Cuboid volume and area derived from those extents agree with the native observations.
- Twenty-four timestamp variants preserve placement across three principal planes and both extrusion directions.
- Ten malformed principal poses fail both public read modes, including wrong-datum and reflected orthonormal matrices.
- Nine unqualified pointer, owner, generation, or non-principal identity controls retain the explicit legacy fallback.
- The regression check requires both public read modes to reject a three-degree in-plane rotation.
- The recorded `example.SLDPRT` keeps Sketch40 on its user-created `Plane1` in both read modes, with an available origin owner and the existing labelled fallback.
- All 58 older pinned SOLIDWORKS part documents serialize identically before and after this repair.
- The focused process and compatibility selection passed 19 tests.
- A multi-sketch native part performs one origin-owner lookup per decode.

Run the production-reader check from the repository root with an unused output path:

```sh
python re/solidworks/FeatureLadderRecovery/CheckPlacement.py --output /tmp/Placement.json
```

The report records the source revision and hashes of all four changed SDK modules.
The shared suite discovers `tests/Research/Archives/Ladders/PlacementTests.py` through its existing planner and shards.
The separate historical recovery verifier still checks the archived 96 centroid failures.

The first merge candidate `651d8287` failed the existing circular-support refusal test.
That test changed the principal-plane identity while retaining its original axis and frame.
The owned principal-reference guard rejects this contradiction before a document can return an unresolved-sketch diagnostic.
The public SDK integration case now requires that format error in full and design-only reads.
The diameter, flags, and footer cases still require unresolved-sketch diagnostics.
The source audit also found the older rectangle attachment mutation expecting fallback after the same principal identity contradiction.
Its public SDK boundary case now requires the format error in both read modes, including permissive inspection.
The [refusal ordering](../../../../Gotchas/Conversion/Solidworks/Readers/PrincipalSupportRefusalOrder.md) records this compatibility distinction.
Fresh remote checks must verify this repair before queue acceptance is claimed.

## Limits

This repair establishes the bounded offline source-placement behavior against recorded native observations.
It does not establish fresh native acceptance or editable cross-format conversion.
The separate typed rectangle reader retains its scene, annotation, and principal-axis admission limits.
Origin-consistent sampling does not establish complete typed archive-map qualification.
Sketches outside the recognized owned principal-reference path retain their existing fallback behavior; this change does not qualify those files.
Neutral explicit mass properties remain unavailable on the legacy path.

[Original field and loader evidence](../../../../../re/solidworks/records/PrincipalSupportCandidates.md)
and [historical recovery findings](../../../../../re/solidworks/FeatureLadderRecovery/SolidWorksPlacementRootCause.json)
remain available independently of this repair.

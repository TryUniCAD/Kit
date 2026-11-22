<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Standalone circular sketch framing

The five original P02 SOLIDWORKS captures have a complete sketch-only history:
zero owned configuration atoms and no body regions, followed by a resolved list
with 18 entries. Resolved lengths are 9,351 bytes for baseline A, 9,579 for baseline
B, the 16 mm diameter edit and inch display, and 9,421 for the YZ source.
The original receipt pins these inputs; independent licensed circle and relation
observations are in
[Circle binding readback](../../../Documentation/Changes/Research/Workers/SolidWorks/CircleBindingReadback.md).

`ReadCircleOnly` walks the system prefix, principal planes, document Origin and
one `moProfileFeature_c` owning `sgSketch`. Existing circular readers consume the
points, sole physical circle, driving diameter, ordered Origin coincidence,
display annotation, region and empty body contour chain. The saved profile
reference resolves an earlier principal datum and its saved axes. This gives
feature 2 for Front sources and feature 4 for the Right Plane YZ source.

The standalone tail requires profile flags `(0, 4)`, a null pointer, state pair
`(-1, 0)`, one retained raw unsigned profile state word, contour mode zero and a
null pointer. One cached trim surface belongs to the profile; one
`moSegmRightTrimEdgeIdRep_c` selects the actual circular member. A zero return,
typed sketch footer and exact end of stream close the history. The raw state word
is preserved as `native_profile_state`; no undocumented semantic meaning is
assigned to it. Unsupported flags, pointers, references or trailing history
prevent this projection. No captured offsets or fixture identities select a
production path.

An exact empty-partition byte fingerprint is not a semantic condition. Baseline B,
the edit and inch sources have different saved partition state while preserving
the same fully framed sketch-only semantics. Configuration ownership and the
complete history establish the empty body roster. A decoded solid BRep contradicts
that roster and explicitly refuses body removal. Retained native and cache
payloads and existing unqualified metadata remain unchanged.

The public boundary tests use all five unchanged originals, actual boss/cut
histories and archive mutations at typed field locations. They also graft an
actual P03 solid partition and actual extra P03 history as contradictions.
These checks are reader evidence; native output and full qualification remain
separate gates. [Change and regression commands](../../../Documentation/Changes/Research/Readers/SolidWorks/StandaloneCircleSketch.md)

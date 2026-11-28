# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.VectorSpace import SpaceVector


# a translated sketch must retain the actual typed datum rather than the compatibility default
def AssertSupport(Document: CadDocument, PlaneId: int) -> None:
    (SketchValue,) = Document.sketches
    assert SketchValue.support_plane_id == f"sldprt:plane:{PlaneId}"
    (Support,) = tuple(
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    assert Support.transform.origin == SpaceVector(0, 0, 0)
    assert Support.transform.z_axis == (
        SpaceVector(1, 0, 0) if PlaneId == 4 else SpaceVector(0, 0, 1)
    )
    assert SketchValue.attributes["support_plane_source"] == "typed-archive-reference"
    (StepValue,) = tuple(
        Value
        for Value in Document.feature_timeline
        if Value.sketch_id == SketchValue.id
    )
    assert StepValue.input_feature_ids == (
        f"sldprt:feature:{PlaneId}",
        "sldprt:feature:5",
    )
    assert Support.provenance is not None and Support.provenance.spans
    assert all(
        SourceSpan.stream == "Contents/Config-0-ResolvedFeatures"
        and SourceSpan.length > 0
        for SourceSpan in Support.provenance.spans
    )

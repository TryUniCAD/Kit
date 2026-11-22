# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.CircularSketch import (
    BindRoundParam,
    BindRoundPlane,
    BindRoundSketch,
)
from convert.adapters.solidworks.Resolved.Circular.CircleOnly import CircleOnly
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# source ownership must agree before replacing the fallback with complete standalone sketch semantics
def BuildSoloDoc(Document: CadDocument, Saved: CircleOnly, Stream: str) -> CadDocument:
    (SketchValue,) = Document.sketches
    Reached = {
        Saved.Profile["feature_id"],
        Saved.Datum.FeatureId,
        Saved.Origin.FeatureId,
    }
    Records = tuple(
        Value
        for Value in Document.feature_timeline
        if Value.attributes.get("native_object_id") in Reached
    )
    Features = {Value.attributes.get("native_object_id"): Value for Value in Records}
    RequireArch(
        len(Features) == len(Records) == len(Reached) == 3,
        True,
        "unique standalone circular feature owners",
    )
    SketchFeature = Features[Saved.Profile["feature_id"]]
    DatumFeature = Features[Saved.Datum.FeatureId]
    OriginFeature = Features[Saved.Origin.FeatureId]
    RequireArch(
        SketchFeature.name == Saved.Profile["name"]
        and SketchFeature.sketch_id == SketchValue.id
        and not SketchFeature.suppressed
        and not SketchFeature.selection_ids
        and DatumFeature.order < SketchFeature.order
        and OriginFeature.order < SketchFeature.order,
        True,
        "standalone circle has its earlier datum and Origin dependencies",
    )
    (Plane,) = tuple(
        Value
        for Value in Document.support_planes
        if Value.attributes.get("native_object_id") == Saved.Datum.FeatureId
    )
    Support = BindRoundPlane(Plane, Saved, Stream)
    Radial = Saved.Diameter
    Diameter = BindRoundParam(
        Document.parameters,
        SketchFeature.id,
        Radial["parameter_name"],
        Radial["diameter_m"],
        Stream,
        Radial["parameter_offset"],
        Radial["native_id"],
        "sketch-diameter-scalar",
    )
    RequireArch(
        SketchFeature.parameter_ids,
        (Diameter.id,),
        "standalone diameter parameter roster",
    )
    Sketch = BindRoundSketch(
        Replace(SketchValue, support_plane_id=Support.id), Saved, Diameter.id, Stream
    )
    Sketch = Replace(
        Sketch,
        attributes=FreezeMapping(
            {**Sketch.attributes, "native_profile_state": Saved.StateWord}
        ),
    )
    SketchStep = Replace(
        SketchFeature,
        input_feature_ids=(DatumFeature.id, OriginFeature.id),
        provenance=Sketch.provenance,
    )
    Result = Replace(
        Document,
        support_planes=tuple(
            Support if Value is Plane else Value for Value in Document.support_planes
        ),
        sketches=(Sketch,),
        feature_timeline=tuple(
            SketchStep if Value is SketchFeature else Value
            for Value in Document.feature_timeline
        ),
        parameters=tuple(
            Diameter if Value.id == Diameter.id else Value
            for Value in Document.parameters
        ),
        bodies=(),
    )
    Result.assert_valid()
    return Result

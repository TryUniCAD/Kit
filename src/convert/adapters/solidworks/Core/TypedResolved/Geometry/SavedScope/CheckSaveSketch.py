from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.MakePrismLines import (
    MakePrismLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import (
    ReadPrismLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineNativeDims import (
    LineNativeDims,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineRules import (
    LineRules,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch


# both projected dimensions must belong to their actual stored sketch handles
def CheckSaveDims(
    Document: CadDocument,
    Profile: FeatureStep,
    SketchValue: Sketch,
    LoopValue: LineLoop,
) -> None:
    Drivers = LineNativeDims(LoopValue.DimsValue)
    Parameters = {
        Parameter.name: Parameter
        for Parameter in Document.parameters
        if Parameter.owner_id == Profile.id
    }
    if set(Parameters) != {"D1", "D2"} or {Driver.name for Driver in Drivers} != set(
        Parameters
    ):
        raise ValueError("SOLIDWORKS saved first boss lacks both rectangle dimensions")
    IdValues = {Parameter.id for Parameter in Parameters.values()}
    if IdValues != set(SketchValue.parameter_ids) or IdValues != {
        RuleValue.parameter_id
        for RuleValue in SketchValue.constraints
        if RuleValue.kind == "distance"
    }:
        raise ValueError(
            "SOLIDWORKS saved first boss has unresolved rectangle dimensions"
        )
    for Driver in Drivers:
        Parameter = Parameters[Driver.name]
        if (
            Parameter.attributes.get("typed_archive_owner") != Driver.TypedOwner
            or Parameter.value.value != Driver.value_mm
            or Parameter.expression is not None
        ):
            raise ValueError(
                "SOLIDWORKS saved first boss lacks its actual sketch driver"
            )


# rectangle mode needs its original public contour and associated front datum
def CheckSaveSketch(
    Document: CadDocument,
    LinkValue: NativeLink,
    OwnerValue: ExtrudeOwner,
    Profile: FeatureStep,
    Features: Mapping[int, ArchiveNode],
) -> LineLoop:
    (SketchValue,) = Document.sketches
    if SketchValue.suppressed or SketchValue.id != Profile.sketch_id:
        raise ValueError("SOLIDWORKS saved first boss lacks its active sketch")
    ProfileValue = OwnerValue.ProfileValue
    FrameValue = ReadPrismFrame(ProfileValue, LinkValue.ConfigValue.RootValue, Features)
    Reference = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    DatumId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    (PlaneValue,) = (
        Plane
        for Plane in Document.support_planes
        if Plane.id == SketchValue.support_plane_id
    )
    if PlaneValue.id != f"sldprt:plane:{DatumId}" or PlaneValue.transform != FrameValue:
        raise ValueError("SOLIDWORKS saved first boss has a different sketch frame")
    LoopValue = ReadPrismLoop(ProfileValue, LinkValue, IsSaved=True)
    (OrderValue,) = SketchValue.closed_profile_entity_ids
    Entities = {
        Entity.id: Entity.geometry
        for Entity in SketchValue.entities
        if not Entity.construction
    }
    ProfileId = NativeNodeId(ProfileValue)
    if (
        SketchValue.attributes.get("typed_archive_owner") != LoopValue.OwnerValue
        or len(Entities) != 4
        or set(Entities) != set(OrderValue)
        or tuple(Entities[Identity] for Identity in OrderValue)
        != MakePrismLines(LoopValue)
        or SketchValue.attributes.get("native_object_id") != ProfileId
        or SketchValue.constraints != LineRules(ProfileId, LoopValue, tuple(Entities))
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss lacks its complete public contour"
        )
    CheckSaveDims(Document, Profile, SketchValue, LoopValue)
    return LoopValue

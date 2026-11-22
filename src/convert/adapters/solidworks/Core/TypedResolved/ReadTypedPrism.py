from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel, NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismSketch import (
    ReadPrismSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.BindDimLeaf import (
    BindDimLeaf,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.BindLineLoop import (
    BindLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# typed sketch and extrusion reads must retain actual support and dimension scopes
def ReadTypedPrism(
    Model: NativeModel, Archive: SldprtArchive
) -> tuple[NativeSketch, ExtrudeOwner] | None:
    (SketchValue,) = Model.sketches
    (Operation,) = Model.operations
    CheckDims = (
        Operation.kind == "join"
        and Model.active_configuration_id == 0
        and len(Model.configurations) == 1
    )
    HasDims = CheckDims and len(SketchValue.dimensions) == 2
    try:
        LinkValue = ReadNativeLink(
            Archive, Model.active_configuration_id, RectangleDims=CheckDims
        )
        NodesValue = IndexFeatures(LinkValue)
        Profile = RequireNative(NodesValue[SketchValue.object_id], "moProfileFeature_c")
        if CheckDims:
            Geometry = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
            DimsValue = NativeRecord(Geometry.FieldsValue.get("dims"))
            HasDims = HasDims or DimsValue.get("ng2") != 0
        Owner = ReadExtrude(LinkValue, NodesValue[Operation.object_id], NodesValue)
        if Owner.ProfileValue is not Profile:
            raise ValueError("boss does not own its selected sketch")
        LocalSketch = ReadPrismSketch(SketchValue, Profile, LinkValue, NodesValue)
        if not any(
            Plane.object_id == LocalSketch.support_plane_id for Plane in Model.planes
        ):
            raise ValueError("sketch does not own an available support plane")
        if HasDims:
            if Model.equations:
                raise ValueError("dimensioned cold leaf has unqualified equations")
            return BindDimLeaf(LocalSketch, Owner, LinkValue), Owner
        Bound = BindLineLoop(LocalSketch, Profile, LinkValue)
        return None if Bound is None else (Bound, Owner)
    except (KeyError, TypeError, ValueError) as ErrorInfo:
        if HasDims:
            raise SldprtFormat(
                f"invalid typed dimensioned cold leaf: {ErrorInfo}"
            ) from ErrorInfo
        return None

from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import BindDepth, BindExtrude
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Lines.BindLineLoop import BindLineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# unsupported typed modes must stay explicit while established public readers retain their prior behavior
def WithTypedNative(Model: NativeModel, Archive: SldprtArchive) -> NativeModel:
    if (
        ContainerMo(Archive.streams) != 19000
        or KPartitionStream in Archive.streams
        or len(Model.sketches) != 1
        or len(Model.operations) != 1
    ):
        return Model
    SketchValue = Model.sketches[0]
    Operation = Model.operations[0]
    try:
        LinkValue = ReadNativeLink(Archive, Model.active_configuration_id)
        NodesValue = IndexFeatures(LinkValue)
        Profile = RequireNative(NodesValue[SketchValue.object_id], "moProfileFeature_c")
        Owner = ReadExtrude(LinkValue, NodesValue[Operation.object_id], NodesValue)
        if Owner.ProfileValue is not Profile:
            return Model
        FrameValue = ReadPrismFrame(Profile, LinkValue.ConfigValue.RootValue, NodesValue)
        Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
        PlaneId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
        if type(PlaneId) is not int or not any(Plane.object_id == PlaneId for Plane in Model.planes):
            return Model
        Bound = BindLineLoop(ReplaceValue(SketchValue, support_plane_id=PlaneId), Profile, LinkValue)
        if Bound is None:
            return Model
    except (KeyError, TypeError, ValueError):
        return Model
    return ReplaceValue(
        Model,
        sketches=(ReplaceValue(Bound, TypedFrame=FrameValue),),
        features=tuple(
            BindDepth(Feature, Owner) if Feature.object_id == Operation.object_id else Feature
            for Feature in Model.features
        ),
        operations=(BindExtrude(Operation, Owner),),
    )

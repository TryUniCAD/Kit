from dataclasses import replace as ReplaceValue

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Api.Fusion.SavedCuboid.ChangeSnapParts import ChangeSnapParts


# each altered saved document keeps the same geometry to isolate strict ownership validation
def ChangeSnapOwner(Model: DocumentModel, RoleName: str) -> DocumentModel:
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Bodies = ResolveField(Graph, Context.Component, "rBodies", "Bodies")
    CacheBodies = ResolveField(Graph, Context.Component, "rCacheBodies", "Bodies")
    History = ResolveField(Graph, Bodies, "rBRepSerializer", "BRepHistorySerializer")
    Serializer = ResolveField(Graph, CacheBodies, "rBRepSerializer", "BRepSerializer")
    if RoleName == "history_owner":
        return ChangeField(
            Model, History.ObjectId, "rBodies", LocalRef(CacheBodies.ObjectId)
        )
    if RoleName == "snapshot_owner":
        return ChangeField(
            Model, Serializer.ObjectId, "rBodies", LocalRef(Bodies.ObjectId)
        )
    if RoleName == "serializer":
        return ChangeField(
            Model, CacheBodies.ObjectId, "rBRepSerializer", LocalRef(History.ObjectId)
        )
    if RoleName in ("missing_part", "part_name", "extra_part", "root_with_extra"):
        Model = ChangeSnapParts(Model, RoleName)
        if RoleName != "root_with_extra":
            return Model
    ToolNode = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    (Cache,) = LinkedNodes(Graph, ToolNode, "toolbodyCaches")
    if RoleName in ("root_id", "root_with_extra"):
        return ChangeField(Model, Cache.ObjectId, "cachedEntityId", 987654321)
    if RoleName != "scope_asset":
        raise ValueError("Unknown saved snapshot mutation role")
    Scope = Cache.Fields["scope"]
    assert isinstance(Scope, ValueObject)
    (Group,) = Scope.Groups
    Fields = tuple(
        (
            ReplaceValue(Field, Value="01234567-89ab-cdef-0123-456789abcdef")
            if Field.FieldName == "assetId"
            else Field
        )
        for Field in Group.Fields
    )
    return ChangeField(
        Model,
        Cache.ObjectId,
        "scope",
        ReplaceValue(Scope, Groups=(ReplaceValue(Group, Fields=Fields),)),
    )

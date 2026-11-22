from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, TextValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the design serializer must own exactly the current live geometry body
def CheckSpanStore(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    BodyValue: BodyNode,
) -> None:
    SameNodes((Context.BodyNode,), Graph.ByClass("Body"))
    SameNodes((Context.DcBody,), Graph.ByClass("DcBody"))
    SameNodes((Context.DcBody,), LinkedNodes(Graph, Context.Fragment, "dcBodies"))
    if (
        Graph.Resolve(Context.DcBody.Fields["rOwnFeature"]) != Context.Extrude
        or Context.DcBody.Fields["bodyUuid"] != Context.BodyNode.Fields["persistentId"]
    ):
        raise ValueError("Native circular span body ownership disagrees")
    Bodies = ResolveField(Graph, Context.Component, "rBodies", "Bodies")
    SameNodes((Context.BodyNode,), LinkedNodes(Graph, Bodies, "children"))
    SameNodes((Context.BodyNode,), LinkedNodes(Graph, Bodies, "groupChildren"))
    Serializer = ResolveField(Graph, Bodies, "rBRepSerializer", "BRepHistorySerializer")
    RequireFields(Serializer, {"rBodies": LocalRef(Bodies.ObjectId), "rBody": None})
    Entries = MappingItems(Serializer.Fields["mapBodyId"])
    if (
        len(Entries) != 1
        or IntegerValue(Entries[0].First) != BodyValue.Prefix.EntityTag
        or IntegerValue(Entries[0].Second) != Context.BodyNode.ObjectId
        or Model.Bodies[0].PartName
        != "Breps.BlobParts/" + TextValue(Serializer.Fields["partName"])
    ):
        raise ValueError("Native circular span serializer disagrees with the live body")
    RequireFields(
        Context.BodyNode,
        {"bodyType": 2, "rOwningDeriveFeature": None, "overriddenBody": None},
    )

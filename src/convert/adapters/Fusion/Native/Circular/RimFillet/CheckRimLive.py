from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimStates import (
    ReadRimStates,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimGeo import CheckRimGeo
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimAttrs import (
    CheckRimAttrs,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimLinks import (
    CheckRimLinks,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimRecipe import (
    CheckRimRecipe,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimBaseTags import (
    ReadRimBaseTags,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimTags import CheckRimTags
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanStore import CheckSpanStore
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanBody import ReadSpanBody
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# strict live admission composes source geometry attribution and selected predecessor identity without changing either state
def CheckRimLive(
    Model: DocumentModel, Graph: NativeGraph, Context: RimContext, Shape: CircleShape
) -> tuple[GeometryState, GeometryState]:
    if Shape.Geometry.center.x != 0 or Shape.Geometry.center.y != 0:
        raise ValueError("Native rim requires the qualified origin-centered profile")
    Prior, Current = ReadRimStates(Model, Context)
    Height = NumberValue(Context.Extrusion.Along.Fields["value"]) * 10
    Fillet = NumberValue(Context.Radius.Fields["value"]) * 10
    if Fillet <= 0:
        raise ValueError("Native rim requires a positive constant fillet radius")
    PriorFaces, PriorEdges = CheckRimGeo(Prior, Shape.Geometry.radius, Height, 0.0)
    FinalFaces, FinalEdges = CheckRimGeo(Current, Shape.Geometry.radius, Height, Fillet)
    for State, Edges in ((Prior, PriorEdges), (Current, FinalEdges)):
        CheckRimAttrs(State)
        CheckRimLinks(State, Shape, Edges["bottom"])
    CheckRimRecipe(Prior, Context, PriorFaces, PriorEdges)
    BodyTag, TagSet, Rounding = ReadRimBaseTags(
        Graph, Context, Shape, Prior, PriorFaces, PriorEdges
    )
    CheckRimTags(
        Graph, Context, Current, FinalFaces, FinalEdges, BodyTag, TagSet, Rounding
    )
    BodyValue, _ = ReadSpanBody(Current)
    CheckSpanStore(Graph, Context.Extrusion, Model, BodyValue)
    return Prior, Current

from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    SameNodes,
    LinkedNodes,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext


# scoped validators are complete only when their union covers every native profile and datum reference
def CheckCutRefs(
    Graph: NativeGraph, Contexts: tuple[ExtrudeContext, ExtrudeContext]
) -> None:
    Profiles = tuple(
        Value
        for Context in Contexts
        for Value in LinkedNodes(Graph, Context.Extrude, "profileDataRefs")
    )
    Targets = LinkedNodes(Graph, Contexts[1].Extrude, "targetDataRefs")
    SameNodes((*Profiles, *Targets), Graph.ByClass("ModelDataRef"))
    SameNodes(
        tuple(
            Value
            for Profile in Profiles
            for Value in LinkedNodes(Graph, Profile, "dataRefs")
        ),
        Graph.ByClass("SketchRegionRef"),
    )
    Matrices = tuple(
        ResolveField(Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix")
        for Context in Contexts
    )
    SameNodes(Matrices, Graph.ByClass("DRMatrix"))
    SameNodes(
        tuple(
            Value
            for Matrix in Matrices
            for Value in LinkedNodes(Graph, Matrix, "dataRefs")
        ),
        Graph.ByClass("EntityDataRef"),
    )
    SameNodes(
        tuple(Context.Plane for Context in Contexts), Graph.ByClass("CoordinateSystem")
    )
    Tables = tuple(
        ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
        for Context in Contexts
    )
    Progenitors = tuple(
        Graph.Resolve(Entry.First)
        for Table in Tables
        for Entry in SeriesItems(Table.Fields["ProgenitorTagVec"])
        if isinstance(Entry, ValuePair)
    )
    SameNodes(
        Progenitors,
        (*Graph.ByClass("SketchCurveProgenitor"), *Graph.ByClass("BodyProgenitor")),
    )
    SameNodes(
        tuple(
            ResolveField(Graph, NodeValue, "rRecipe", "SketchCurveRecipe")
            for NodeValue in Progenitors
            if NodeValue.ClassName == "SketchCurveProgenitor"
        ),
        Graph.ByClass("SketchCurveRecipe"),
    )

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import pi as CirclePi
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.Sketch import SketchRelation
from convert.adapters.Fusion.Native.Rectangle.CheckRectDeps import CheckRectDeps
from convert.adapters.Fusion.Native.Rectangle.ReadRectDim import ReadRectDim

# the supported source table binds the length drivers along with blind depth and explicit zero taper
KRectParams = ("width_mm", "height_mm", "depth_mm", "d4")


# exact allocation and paired observer ranks keep the four native drivers in their original roles
def ReadRectDims(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Dimensions: tuple[NativeNode, ...],
    Lines: tuple[NativeNode, ...],
    Anchor: NativeNode,
    Reverse: bool = False,
    YzDatum: bool = False,
    AllowTaper: bool = False,
) -> tuple[tuple[NativeNode, ...], tuple[NativeNode, ...], tuple[SketchRelation, ...]]:
    SketchBindings = LinkedNodes(Graph, Context.SketchFeature, "dcParameters")
    if len(SketchBindings) != 2:
        raise ValueError("Native constrained rectangle requires two sketch bindings")
    Bindings = (*SketchBindings, Context.Along, Context.Taper)
    SameNodes(Bindings, Graph.ByClass("DcDoubleParameter"))
    Owners = (Context.SketchFeature,) * 2 + (Context.Extrude,) * 2
    Table = ResolveField(Graph, Context.Component, "rParameterTable", "ParameterTable")
    DcNodes = ResolveField(Graph, Context.Fragment, "rNodes", "DcNodes")
    Children = LinkedNodes(Graph, DcNodes, "children")
    if any(Children.count(Binding) != 1 for Binding in Bindings):
        raise ValueError(
            "Native constrained rectangle bindings are absent from the fragment"
        )
    Params = tuple(
        CheckRectBind(
            Graph,
            Binding,
            Owner,
            Table,
            DcNodes,
            SlotValue,
            Reverse and SlotValue == 3,
            AllowTaper,
        )
        for SlotValue, (Binding, Owner) in enumerate(
            zip(Bindings, Owners, strict=True), start=1
        )
    )
    CheckRectIndex(Graph, Context, Table, Params)
    CheckRectDeps(Graph, Context, SketchBindings)
    Kinds = (ConstraintKind.KDistanceX, ConstraintKind.KDistanceY)
    Relations = tuple(
        ReadRectDim(
            Graph, Context, Dimension, Binding, Param, Lines, Anchor, KindValue, YzDatum
        )
        for Dimension, Binding, Param, KindValue in zip(
            Dimensions, SketchBindings, Params[:2], Kinds, strict=True
        )
    )
    Ranks = tuple(
        Dimension.Frame.Subjects[0].ObserverIndex
        for Dimension in Dimensions
        if Dimension.Frame.Subjects
    )
    if Ranks not in ((2, 3), (4, 5)):
        raise ValueError("Native rectangle dimension settings observer ranks disagree")
    if YzDatum and Ranks != (4, 5):
        raise ValueError("Native YZ dimension settings observer ranks disagree")
    return SketchBindings, Params[:2], Relations


# every saved binding and its update must return to the expected feature and parameter table
def CheckRectBind(
    Graph: NativeGraph,
    Binding: NativeNode,
    Owner: NativeNode,
    Table: NativeNode,
    DcNodes: NativeNode,
    SlotValue: int,
    Reverse: bool = False,
    AllowTaper: bool = False,
) -> NativeNode:
    Param = ResolveField(Graph, Binding, "parameter", "Parameter")
    Update = ResolveField(Graph, Binding, "rDynamicUpdateData", "DynamicUpdateData")
    RequireFields(
        Binding,
        {
            "rrOwnerFeature": LocalRef(Owner.ObjectId),
            "rParentFeature": LocalRef(Owner.ObjectId),
            "rParent": LocalRef(DcNodes.ObjectId),
            "rparamId": SlotValue,
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
            "rGroupRepresentative": None,
        },
    )
    RequireFields(
        Param,
        {
            "rParent": LocalRef(Table.ObjectId),
            "dcParameter": LocalRef(Binding.ObjectId),
            "creationIndex": SlotValue,
            "userName": KRectParams[SlotValue - 1],
            "unit": "deg" if SlotValue == 4 else "mm",
            "isUserDefined": False,
            "isDriven": False,
            "group": None,
            "rClientObject": None,
        },
    )
    RequireFields(
        Update,
        {
            "rOwnerNode": LocalRef(Binding.ObjectId),
            "isBodyOK": False,
            "isPredecessorOK": False,
            "xRefPredecessorsHash": 0,
        },
    )
    EmptyFields(Update, ("bodies", "predecessors"))
    Amount = NumberValue(Param.Fields["value"])
    if Amount != NumberValue(Binding.Fields["value"]) or (
        (not -CirclePi / 2 < Amount < CirclePi / 2 if AllowTaper else Amount != 0.0)
        if SlotValue == 4
        else (Amount >= 0.0 if Reverse else Amount <= 0.0)
    ):
        raise ValueError(
            "Native rectangle saved driver values or taper bounds disagree"
            if AllowTaper
            else "Native rectangle saved driver values or zero taper disagree"
        )
    return Param


# the named table and its observer roster cannot include a second driver or hidden global alias
def CheckRectIndex(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Table: NativeNode,
    Params: tuple[NativeNode, ...],
) -> None:
    SameNodes(Params, Graph.ByClass("Parameter"))
    if LinkedNodes(Graph, Table, "children") != Params:
        raise ValueError("Native rectangle model parameter order differs")
    RequireFields(Table, {"highWaterMark": 4})
    RequireFields(Context.Fragment, {"nextParamId": 4})
    Index = ResolveField(
        Graph, Table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    Entries = MappingItems(Index.Fields["parameterMap"])
    if len(Entries) != 4 or {
        Entry.First: Graph.Resolve(Entry.Second) for Entry in Entries
    } != dict(zip(KRectParams, Params, strict=True)):
        raise ValueError("Native rectangle named parameter inventory disagrees")
    Subjects = tuple(
        (Graph.Resolve(Subject.Target), Subject.ObserverIndex)
        for Subject in Index.Frame.Subjects or ()
    )
    if Subjects != tuple((NodeValue, 0) for NodeValue in (Table, *Params)):
        raise ValueError("Native rectangle parameter name index observers disagree")

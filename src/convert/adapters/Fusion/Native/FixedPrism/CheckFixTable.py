from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Parameters.ParamExpression import ParamExpression
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# parameter expressions must connect the three distinct user drivers to their owned model slots
def CheckFixTable(
    Graph: NativeGraph, Table: NativeNode, Params: tuple[NativeNode, ...]
) -> None:
    ParamRows = LinkedNodes(Graph, Table, "children")
    SameNodes(ParamRows, Graph.ByClass("Parameter"))
    Catalog = {TextValue(Param.Fields["userName"]): Param for Param in ParamRows}
    if len(ParamRows) != 7 or len(Catalog) != len(ParamRows) or "" in Catalog:
        raise ValueError(
            "Native fixed rectangle requires seven distinct parameter names"
        )
    RequireFields(Table, {"highWaterMark": len(ParamRows)})
    for Index, Param in enumerate(ParamRows, start=1):
        RequireFields(
            Param, {"rParent": LocalRef(Table.ObjectId), "creationIndex": Index}
        )
    Drivers = tuple(
        ParamExpression(Param, Catalog).parameter_ids for Param in Params[:3]
    )
    Users = tuple(Param for Param in ParamRows if Param.Fields["isUserDefined"] is True)
    SameNodes(ParamRows, (*Users, *Params))
    if len(Users) != 3 or set(Drivers) != {(Param.Identity,) for Param in Users}:
        raise ValueError(
            "Native fixed rectangle lacks three distinct user driver bindings"
        )
    for Param in Users:
        RequireFields(
            Param, {"dcParameter": None, "group": None, "rClientObject": None}
        )
    Search = ResolveField(
        Graph, Table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    Entries = MappingItems(Search.Fields["parameterMap"])
    Subjects = tuple(
        (Graph.Resolve(Subject.Target), Subject.ObserverIndex)
        for Subject in Search.Frame.Subjects or ()
    )

    # allocation order must retain the same parameter observer identities after a vendor save
    Allocated = tuple(sorted(ParamRows, key=lambda Param: Param.ObjectId))
    Expected = tuple(
        tuple((Param, 0) for Param in (Table, *Order))
        for Order in (ParamRows, Allocated)
    )
    if (
        len(Entries) != len(Catalog)
        or {Entry.First: Graph.Resolve(Entry.Second) for Entry in Entries} != Catalog
        or Subjects not in Expected
    ):
        raise ValueError(
            "Native fixed rectangle parameter index disagrees with its table"
        )

from convert.adapters.Fusion.Native.Parameters.CheckBinding import CheckBinding
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    SameNodes,
    LinkedNodes,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ProjectParam
from interchange.Records.RecordParameter import Parameter


# separate feature owners preserve distance and taper edits across the modifying history
def ReadCutParams(
    Graph: NativeGraph, Contexts: tuple[ExtrudeContext, ExtrudeContext]
) -> tuple[Parameter, ...]:
    Table = ResolveField(
        Graph, Contexts[0].Component, "rParameterTable", "ParameterTable"
    )
    Nodes = LinkedNodes(Graph, Table, "children")
    SameNodes(Nodes, Graph.ByClass("Parameter"))
    Catalog = {TextValue(Value.Fields["userName"]): Value for Value in Nodes}
    if len(Catalog) != len(Nodes) or "" in Catalog:
        raise ValueError("Native cut parameter names are not unique")
    Bindings = tuple(
        Value for Context in Contexts for Value in (Context.Along, Context.Taper)
    )
    SameNodes(Bindings, Graph.ByClass("DcDoubleParameter"))
    IdValues = tuple(IntegerValue(Value.Fields["rparamId"]) for Value in Bindings)
    if (
        len(set(IdValues)) != 4
        or min(IdValues) <= 0
        or max(IdValues) > IntegerValue(Contexts[0].Fragment.Fields["nextParamId"])
    ):
        raise ValueError("Native cut parameter allocation is inconsistent")
    Owners: dict[str, NativeNode] = {}
    for Context in Contexts:
        Along, Taper = CheckBinding(Graph, Context.Along, Context), CheckBinding(
            Graph, Context.Taper, Context
        )
        if (
            Along.Fields["name"] != "AlongDistance"
            or Along.Fields["unit"] != "mm"
            or NumberValue(Along.Fields["value"]) <= 0
            or Taper.Fields["name"] != "TaperAngle"
            or Taper.Fields["unit"] != "deg"
            or NumberValue(Taper.Fields["value"]) != 0
        ):
            raise ValueError("Native cut requires positive untapered distance controls")
        Owners.update(
            {Along.Identity: Context.Extrude, Taper.Identity: Context.Extrude}
        )
    return tuple(
        ProjectParam(Value, Catalog, Owners.get(Value.Identity)) for Value in Nodes
    )

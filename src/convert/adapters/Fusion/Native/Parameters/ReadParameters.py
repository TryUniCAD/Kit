from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Parameters.ParamExpression import ParamExpression
from convert.adapters.Fusion.Native.Rectangle.RectContext import RectContext
from interchange.enums.EnumValues import ValueKind
from interchange.records.RecordParameter import Parameter, ParameterValue


def ReadParameters(Graph: NativeGraph, Context: RectContext) -> tuple[Parameter, ...]:
    Table = ResolveField(Graph, Context.Component, "rParameterTable", "ParameterTable")
    Nodes = LinkedNodes(Graph, Table, "children")
    SameNodes(Nodes, Graph.ByClass("Parameter"))
    Catalog = {
        TextValue(NodeValue.Fields["userName"]): NodeValue for NodeValue in Nodes
    }
    if len(Catalog) != len(Nodes) or "" in Catalog:
        raise ValueError("Native parameter names must be nonempty and unique")
    Along = CheckBinding(Graph, Context.Along, Context)
    Taper = CheckBinding(Graph, Context.Taper, Context)
    SameNodes((Context.Along, Context.Taper), Graph.ByClass("DcDoubleParameter"))
    ParameterIds = tuple(
        IntegerValue(NodeValue.Fields["rparamId"])
        for NodeValue in (Context.Along, Context.Taper)
    )
    if (
        len(set(ParameterIds)) != 2
        or min(ParameterIds) <= 0
        or max(ParameterIds) > IntegerValue(Context.Fragment.Fields["nextParamId"])
    ):
        raise ValueError(
            "Native parameter identifiers disagree with their fragment allocator"
        )
    if (
        Along.Fields["unit"] != "mm"
        or Taper.Fields["unit"] != "deg"
        or NumberValue(Along.Fields["value"]) <= 0
        or NumberValue(Taper.Fields["value"]) != 0
    ):
        raise ValueError(
            "Native rectangle extrusion requires positive distance and zero taper"
        )
    return tuple(
        ProjectParam(NodeValue, Catalog, Context, NodeValue in (Along, Taper))
        for NodeValue in Nodes
    )


def CheckBinding(
    Graph: NativeGraph, Binding: NativeNode, Context: RectContext
) -> NativeNode:
    RequireFields(Binding, {"isActive": True, "isEdited": False, "isEliminated": False})
    if (
        Graph.Resolve(Binding.Fields["rrOwnerFeature"]) != Context.Extrude
        or Graph.Resolve(Binding.Fields["rParentFeature"]) != Context.Extrude
    ):
        raise ValueError("Native extrusion parameter owner is inconsistent")
    Parameter = ResolveField(Graph, Binding, "parameter", "Parameter")
    if Graph.Resolve(Parameter.Fields["dcParameter"]) != Binding:
        raise ValueError("Native parameter binding is not reciprocal")
    SameNumbers(
        (NumberValue(Parameter.Fields["value"]),),
        (NumberValue(Binding.Fields["value"]),),
    )
    return Parameter


def ProjectParam(
    NodeValue: NativeNode,
    Catalog: dict[str, NativeNode],
    Context: RectContext,
    IsOwned: bool,
) -> Parameter:
    RequireFields(
        NodeValue,
        {
            "isDirty": False,
            "isDriven": False,
            "isOrphan": False,
            "expressionType": 0,
            "booleanValue": False,
            "textValue": "",
            "isUserDefined": not IsOwned,
        },
    )
    if NodeValue.Fields.get("isExternal", False) is not False or (
        not IsOwned and NodeValue.Fields["dcParameter"] is not None
    ):
        raise ValueError("Unsupported external or owner-linked user parameter")
    UnitName = TextValue(NodeValue.Fields["unit"])
    if UnitName not in ("mm", "deg"):
        raise ValueError("Unsupported native parameter unit")
    Amount = NumberValue(NodeValue.Fields["value"])
    Value = ParameterValue(
        Amount * 10 if UnitName == "mm" else Amount,
        ValueKind.KLength if UnitName == "mm" else ValueKind.KAngle,
        "mm" if UnitName == "mm" else "rad",
    )
    return Parameter(
        NodeValue.Identity,
        TextValue(NodeValue.Fields["userName"]),
        Value,
        expression=ParamExpression(NodeValue, Catalog),
        owner_id=Context.Extrude.Identity if IsOwned else "",
        attributes={
            "comment": TextValue(NodeValue.Fields["comment"]),
            "native_name": TextValue(NodeValue.Fields["name"]),
        },
    )

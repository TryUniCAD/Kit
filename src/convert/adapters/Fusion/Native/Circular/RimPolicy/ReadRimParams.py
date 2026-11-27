from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimBinding import (
    CheckRimBinding,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ProjectWeight import (
    ProjectWeight,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ProjectParam
from interchange.Records.RecordParameter import Parameter


# exact role coverage preserves all four driving values and any independently retained user parameters
def ReadRimParams(Graph: NativeGraph, Context: RimContext) -> tuple[Parameter, ...]:
    Extrusion = Context.Extrusion
    Table = ResolveField(
        Graph, Extrusion.Component, "rParameterTable", "ParameterTable"
    )
    Values = LinkedNodes(Graph, Table, "children")
    SameNodes(Values, Graph.ByClass("Parameter"))
    Catalog = {TextValue(Value.Fields["userName"]): Value for Value in Values}
    if len(Catalog) != len(Values) or "" in Catalog:
        raise ValueError("Native rim parameter names must be unique and nonempty")
    Bindings = (Extrusion.Along, Extrusion.Taper, Context.Weight, Context.Radius)
    SameNodes(Bindings, Graph.ByClass("DcDoubleParameter"))
    Identities = tuple(IntegerValue(Value.Fields["rparamId"]) for Value in Bindings)
    if (
        len(set(Identities)) != 4
        or min(Identities) <= 0
        or max(Identities) > IntegerValue(Extrusion.Fragment.Fields["nextParamId"])
    ):
        raise ValueError(
            "Native rim parameter identifiers disagree with their allocator"
        )
    Nodes = ResolveField(Graph, Extrusion.Fragment, "rNodes", "DcNodes")
    Parameters = tuple(
        CheckRimBinding(Graph, Binding, Owner, Table, Nodes, RoleName, UnitName)
        for Binding, Owner, RoleName, UnitName in zip(
            Bindings,
            (Extrusion.Extrude, Extrusion.Extrude, Context.Feature, Context.Feature),
            ("AlongDistance", "TaperAngle", "TangencyWeight", "Radius"),
            ("mm", "deg", "", "mm"),
            strict=True,
        )
    )
    Owners = {
        Value.Identity: Owner
        for Value, Owner in zip(
            Parameters,
            (Extrusion.Extrude, Extrusion.Extrude, Context.Feature, Context.Feature),
            strict=True,
        )
    }
    for Value in Values:
        if Value not in Parameters:
            RequireFields(
                Value,
                {
                    "dcParameter": None,
                    "isUserDefined": True,
                    "rClientObject": None,
                    "group": None,
                },
            )
            if Graph.Resolve(Value.Fields["rParent"]) != Table:
                raise ValueError("Native rim user parameter belongs to another table")
    if (
        NumberValue(Extrusion.Along.Fields["value"]) <= 0
        or NumberValue(Extrusion.Taper.Fields["value"]) != 0
        or not 0
        < NumberValue(Context.Radius.Fields["value"])
        < ReadCircle(Graph, Extrusion).Geometry.radius / 10
    ):
        raise ValueError("Native rim radius or extrusion dimensions are unsupported")
    return tuple(
        (
            ProjectWeight(Value, Context.Feature)
            if Value == Context.WeightParam
            else ProjectParam(Value, Catalog, Owners.get(Value.Identity))
        )
        for Value in Values
    )

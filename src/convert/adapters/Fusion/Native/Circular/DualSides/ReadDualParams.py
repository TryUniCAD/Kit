from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters
from interchange.Records.RecordParameter import Parameter


# independent taper controls retain their actual typed owners instead of an effective cone
def ReadDualParams(
    Graph: NativeGraph, Context: ExtrudeContext
) -> tuple[Parameter, ...]:
    for FieldName, RoleName in (
        ("rAlongDistance", "AlongDistance"),
        ("rAgainstDistance", "AgainstDistance"),
        ("rTaperAngle", "TaperAngle"),
        ("side2TaperAngle", "Side2TaperAngle"),
    ):
        Binding = ResolveField(Graph, Context.Extrude, FieldName, "DcDoubleParameter")
        ParameterNode = ResolveField(Graph, Binding, "parameter", "Parameter")
        if ParameterNode.Fields["name"] != RoleName:
            raise ValueError("Native circular side parameter role is inconsistent")
    return ReadParameters(Graph, Context, AllowTaper=True, AllowBothTaper=True)

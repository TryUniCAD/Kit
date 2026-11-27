from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Parameters.CheckBinding import CheckBinding


# each extent role must retain its own reciprocal parameter before neutral projection
def ReadExtentBind(
    Graph: NativeGraph, Context: ExtrudeContext
) -> tuple[NativeNode, ...]:
    ExtentBindings: tuple[NativeNode, ...] = (Context.Along, Context.Taper)
    if Context.Extrude.Fields["rAgainstDistance"] is not None:
        ExtentBindings += (
            ResolveField(
                Graph, Context.Extrude, "rAgainstDistance", "DcDoubleParameter"
            ),
            ResolveField(
                Graph, Context.Extrude, "side2TaperAngle", "DcDoubleParameter"
            ),
        )
        Against = CheckBinding(Graph, ExtentBindings[2], Context)
        SecondTaper = CheckBinding(Graph, ExtentBindings[3], Context)
        if (
            Against.Fields["unit"] != "mm"
            or NumberValue(Against.Fields["value"]) <= 0
            or SecondTaper.Fields["unit"] != "deg"
            or NumberValue(SecondTaper.Fields["value"]) != 0
        ):
            raise ValueError("Unsupported native second side distance or taper")
    if Context.Extrude.Fields["profileOffset"] is not None:
        OffsetBinding = ResolveField(
            Graph, Context.Extrude, "profileOffset", "DcDoubleParameter"
        )
        OffsetParam = CheckBinding(Graph, OffsetBinding, Context)
        RequireFields(OffsetParam, {"name": "ProfileOffset", "unit": "mm"})
        ExtentBindings += (OffsetBinding,)
    return ExtentBindings

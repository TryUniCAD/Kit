from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields, ResolveField
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ReadExtentMode import ReadExtentMode


# offset placement requires its own typed binding without admitting other start or feature families
def CheckExtStart(
    Graph: NativeGraph, Context: ExtrudeContext, AllowOffset: bool = False
) -> None:
    Feature = Context.Extrude
    StartKind = IntegerValue(Feature.Fields["profileLocaltionType"])
    if StartKind == 0 or not AllowOffset:
        RequireFields(Feature, {"profileLocaltionType": 0, "profileOffset": None})
        return
    RequireFields(Feature, {"profileLocaltionType": 1, "booleanOperation": 4})
    if ReadExtentMode(Feature) != "two_sided" or len(Graph.ByClass("CircArc3D")) != 1:
        raise ValueError("Native offset start requires a two sided circular create")
    RequireFields(Context.Taper, {"value": 0.0})
    SecondTaper = ResolveField(Graph, Feature, "side2TaperAngle", "DcDoubleParameter")
    RequireFields(SecondTaper, {"value": 0.0})
    Binding = ResolveField(Graph, Feature, "profileOffset", "DcDoubleParameter")
    Parameter = ResolveField(Graph, Binding, "parameter", "Parameter")
    RequireFields(Parameter, {"name": "ProfileOffset", "unit": "mm"})

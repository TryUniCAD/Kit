from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.RimPolicy.SelectRimBase import (
    SelectRimBase,
)
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue


# selected source references must remain original so geometry never infers a replacement edge
def ReadRimContext(Graph: NativeGraph) -> RimContext:
    Extrusion, Feature = SelectRimBase(Graph)
    Values = LinkedNodes(Graph, Feature, "filletEdgeData")
    if len(Values) != 1 or Values[0].ClassName != "DcFilletEdgeData":
        raise ValueError("Native rim fillet requires one constant edge data owner")
    EdgeData = Values[0]
    SameNodes((EdgeData,), Graph.ByClass("DcFilletEdgeData"))
    Selected = ResolveField(Graph, EdgeData, "connectedEdgeRef", "ModelDataRef")
    Values = LinkedNodes(Graph, Selected, "dataRefs")
    if len(Values) != 1 or Values[0].ClassName != "BrepRef":
        raise ValueError("Native rim fillet requires one selected brep reference")
    SelectedRef = Values[0]
    RecipeNode = ResolveField(Graph, SelectedRef, "rRecipe", "ASMRecipe")
    Recipe = RecipeNode.Fields["m_Recipe"]
    if not isinstance(Recipe, OptionalValue) or not isinstance(
        Recipe.Value, RecipeValue
    ):
        raise ValueError("Native rim selection requires a complete typed recipe")
    Radius = ResolveField(Graph, EdgeData, "radiusValue", "DcDoubleParameter")
    Weight = ResolveField(Graph, EdgeData, "tangencyWeight", "DcDoubleParameter")
    return RimContext(
        Extrusion,
        Feature,
        EdgeData,
        SelectedRef,
        Recipe.Value,
        Radius,
        ResolveField(Graph, Radius, "parameter", "Parameter"),
        Weight,
        ResolveField(Graph, Weight, "parameter", "Parameter"),
    )

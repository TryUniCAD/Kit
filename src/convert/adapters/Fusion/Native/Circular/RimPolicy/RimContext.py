from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue


# original source owners keep selection and geometry checks tied to the same feature graph
@MakeDataClass(frozen=True, slots=True)
class RimContext:
    Extrusion: ExtrudeContext
    Feature: NativeNode
    EdgeData: NativeNode
    SelectedRef: NativeNode
    Recipe: RecipeValue
    Radius: NativeNode
    RadiusParam: NativeNode
    Weight: NativeNode
    WeightParam: NativeNode

from struct import pack as PackValues
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeAngleValue import (
    MakeAngleValue,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionView import (
    MakeExtrudeView,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import (
    InitNodeMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the modern end needs its actual local driving parameter dimension retaining handle and model dependent display descriptor
def MakeRevAngleMut(
    FeatureValue: ArchiveNode,
    InputValue: PartBuildInput,
    PlanValue: RevolvePlan,
    Allocator: PersistentIds,
    *,
    Against: bool = False,
) -> DimensionGraph:
    AngleValue = PlanValue.AgainstAngle if Against else PlanValue.AngleValue
    if AngleValue is None:
        raise ValueError("second revolve display requires its own angular driver")
    Parameter = ArchiveNode(RuntimeClass("moAngleParameter_c", 1), {})
    InitNodeMut(Parameter, "D2" if Against else "D1")
    Parameter.FieldsValue.update(
        {
            "owner": FeatureValue,
            "f0c": 0,
            "f48": None,
            "f58": AngleValue,
            "f68": 0,
        }
    )
    Dimension = MakeAngleValue(FeatureValue, Parameter)
    _ = Allocator.AllocateMut(Dimension, "f50")
    HandleValue = MakeHandleMut(FeatureValue, Dimension)
    DisplayValue = MakeExtrudeView(
        FeatureValue,
        HandleValue,
        True,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    if Against:
        DisplayValue.FieldsValue["f1018"] = (
            FieldInt(DisplayValue.FieldsValue, "f1018") | 4
        )
    ArrayValue = CastValue(dict[str, object], DisplayValue.FieldsValue["f5b0"])
    ArrayValue["data"] = PackValues("<d", AngleValue)
    return DimensionGraph(Parameter, Dimension, HandleValue, DisplayValue)

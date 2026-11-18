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
    MakeExtrusionView,
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


# the modern end needs its actual local driving parameter dimension retaining handle and model dependent display descriptor
def MakeRevAngleMut(
    FeatureValue: ArchiveNode,
    InputValue: PartBuildInput,
    PlanValue: RevolvePlan,
    Allocator: PersistentIds,
) -> DimensionGraph:
    Parameter = ArchiveNode(RuntimeClass("moAngleParameter_c", 1), {})
    InitNodeMut(Parameter, "D1")
    Parameter.FieldsValue.update(
        {
            "owner": FeatureValue,
            "f0c": 0,
            "f48": None,
            "f58": PlanValue.AngleValue,
            "f68": 0,
        }
    )
    Dimension = MakeAngleValue(FeatureValue, Parameter)
    _ = Allocator.AllocateMut(Dimension, "f50")
    HandleValue = MakeHandleMut(FeatureValue, Dimension)
    DisplayValue = MakeExtrusionView(
        FeatureValue,
        HandleValue,
        True,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    ArrayValue = CastValue(dict[str, object], DisplayValue.FieldsValue["f5b0"])
    ArrayValue["data"] = PackValues("<d", PlanValue.AngleValue)
    return DimensionGraph(Parameter, Dimension, HandleValue, DisplayValue)

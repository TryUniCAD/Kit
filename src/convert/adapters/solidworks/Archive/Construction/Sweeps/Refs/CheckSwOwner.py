from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# sweep picks must refer to the actual same part principal plane and its installed diameter or radius
def CheckSwOwner(
    SystemValue: PartSystem,
    ProfileValue: ArchiveNode,
    AxisValue: Literal["x", "z"],
    DriverValue: DimensionGraph,
) -> None:
    FieldsValue = ProfileValue.FieldsValue
    if (
        ProfileValue.ClassValue != RuntimeClass("moProfileFeature_c", 1)
        or FieldsValue["owner"] is not SystemValue.RootValue
    ):
        raise ValueError("sweep pick requires the actual same part profile")
    SketchValue = ArchiveNode.RequireNode(FieldsValue["pd_f80"])
    SupportValue = ArchiveNode.RequireNode(FieldsValue["pd_f78"])
    SupportId = NativeNodeId(SystemValue.SystemValues.PlaneValues[AxisValue])
    OwnerValue = RequireRecord(SupportValue.FieldsValue["ff0"])
    Dimensions = RequireRecord(SketchValue.FieldsValue["dims"])
    (DriverRow,) = ReadRows(Dimensions["val_g1"])
    if (
        FieldInt(OwnerValue, "f00") != SupportId
        or DriverRow["d"] is not DriverValue.DimensionValue
        or FieldInt(DriverValue.DimensionValue.FieldsValue, "f80")
        != (15 if AxisValue == "x" else 3)
        or DriverValue.DimensionValue.FieldsValue["f28"]
        is not DriverValue.ParameterValue
        or DriverValue.HandleValue.FieldsValue["ff0"] is not SketchValue
    ):
        raise ValueError(
            "sweep pick requires the actual canonical support and installed driver"
        )

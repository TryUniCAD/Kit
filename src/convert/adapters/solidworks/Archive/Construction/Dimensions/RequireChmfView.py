from math import pi as PiValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# chamfer display reuse requires the actual linked local distance or angle factory
def RequireChmfView(
    OwnerValue: ArchiveNode, HandleValue: ArchiveNode, TextKind: int
) -> None:
    IsAngle = TextKind == 13
    Dimension = ArchiveNode.RequireNode(HandleValue.FieldsValue.get("ff0"))
    Parameter = ArchiveNode.RequireNode(Dimension.FieldsValue.get("f28"))
    ScalarValue = RequireScalar(Parameter.FieldsValue.get("f58"))
    NameValue = ReadNodeName(Parameter)
    if (
        OwnerValue.ClassValue != RuntimeClass("Chamfer_c", 1)
        or type(TextKind) is not int
        or TextKind not in (18, 13)
        or FieldInt(OwnerValue.FieldsValue, "f2b0") != 19000
        or FieldInt(OwnerValue.FieldsValue, "f8a0") != 10
        or HandleValue.ClassValue != RuntimeClass("moFeatureDimHandle_c", 1)
        or FieldInt(HandleValue.FieldsValue, "f4c") != 19000
        or any(
            FieldName not in HandleValue.FieldsValue
            or HandleValue.FieldsValue[FieldName] is not None
            for FieldName in ("f58", "fe8", "f100")
        )
        or Dimension.ClassValue
        != RuntimeClass("AngleDim_c" if IsAngle else "ParallelPlaneDistanceDim_c", 1)
        or Parameter.ClassValue
        != RuntimeClass("moAngleParameter_c" if IsAngle else "moLengthParameter_c", 1)
        or Dimension.FieldsValue.get("owner") is not OwnerValue
        or Parameter.FieldsValue.get("owner") is not OwnerValue
        or Dimension.FieldsValue.get("retaining_handles") != (HandleValue,)
        or Dimension.FieldsValue.get("refcount") != 1
        or Parameter.FieldsValue.get("f20") != ""
        or (
            NameValue != ("D2" if IsAngle else "D1")
            and (
                IsAngle or NameValue != "D3" or OwnerValue.FieldsValue.get("f8c0") != 2
            )
        )
        or ScalarValue <= 0
        or (
            IsAngle
            and (ScalarValue >= PiValue / 2 or Dimension.FieldsValue.get("ff8") != 1)
        )
    ):
        raise ValueError("chamfer display requires its actual local mode driver")

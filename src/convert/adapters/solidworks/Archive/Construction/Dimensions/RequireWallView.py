from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)


# the shell distance display refers to its own local wall factory and thickness driver
def RequireWallView(
    OwnerValue: ArchiveNode, HandleValue: ArchiveNode, TextKind: int
) -> None:
    Dimension = RequireNode(HandleValue.FieldsValue.get("ff0"), "ThreeDRadiusDim_c")
    Parameter = RequireNode(Dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    if (
        TextKind != 18
        or FieldInt(OwnerValue.FieldsValue, "f2b0") != 19000
        or FieldInt(HandleValue.FieldsValue, "f4c") != 19000
        or any(
            HandleValue.FieldsValue.get(KeyValue) is not None
            for KeyValue in ("f58", "fe8", "f100")
        )
        or Dimension.FieldsValue.get("owner") is not OwnerValue
        or Dimension.FieldsValue.get("retaining_handles") != (HandleValue,)
        or Parameter.FieldsValue.get("owner") is not OwnerValue
        or ReadNodeName(Parameter) != "D1"
        or RequireScalar(Parameter.FieldsValue.get("f58")) <= 0
    ):
        raise ValueError("wall display requires its actual local driving thickness")

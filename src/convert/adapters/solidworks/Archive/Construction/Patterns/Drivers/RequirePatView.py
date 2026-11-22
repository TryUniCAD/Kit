from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)


# the verified local pattern factory supplies separate native integer and distance display text kinds
def RequirePatView(
    OwnerValue: ArchiveNode, HandleValue: ArchiveNode, TextKind: int
) -> None:
    Integer = TextKind == 0
    if (
        type(TextKind) is not int
        or TextKind not in (0, 18)
        or FieldInt(OwnerValue.FieldsValue, "f2b0") != 19000
    ):
        raise ValueError("pattern display requires the ordinary count or pitch factory")
    Dimension = RequireNode(
        HandleValue.FieldsValue.get("ff0"),
        "moNumberDim_c" if Integer else "ParallelPlaneDistanceDim_c",
    )
    Parameter = RequireNode(
        Dimension.FieldsValue.get("f28"),
        "moIntegerParameter_c" if Integer else "moLengthParameter_c",
    )
    Allowed = ("D1", "D2") if Integer else ("D3", "D4", "D5", "D6")
    if (
        OwnerValue.ClassValue != RuntimeClass("moLPattern_c", 1)
        or Dimension.FieldsValue.get("owner") is not OwnerValue
        or Parameter.FieldsValue.get("owner") is not OwnerValue
        or Dimension.FieldsValue.get("retaining_handles") != (HandleValue,)
        or ReadNodeName(Parameter) not in Allowed
    ):
        raise ValueError(
            "pattern display requires its actual local dimension parameter and retaining handle"
        )

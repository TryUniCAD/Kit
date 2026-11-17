from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# alternate or contextual dimension branches cannot be represented as the ordinary local driving length
def CheckMateParam(Handle: ArchiveNode, Dimension: ArchiveNode) -> None:
    Parameter = RequireNode(Dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    if (
        Handle.FieldsValue.get("fe8") is not None
        or Handle.FieldsValue.get("f100") is not None
        or FieldInt(Parameter.FieldsValue, "f68") != 0
    ):
        raise ValueError(
            "typed mate distance requires the ordinary local parameter branch"
        )

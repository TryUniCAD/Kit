from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepObjectRows import (
    MakeSweepRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# ordinary standard sweep contact binds the sole actual live front path and leaves alternate guides absent
def MakeSwContact(PathValue: ArchiveNode) -> ArchiveNode:
    if (
        PathValue.ClassValue != RuntimeClass("moGeneralCurveRef_w", 1)
        or PathValue.FieldsValue["has_fc8"] != 0
    ):
        raise ValueError(
            "ordinary sweep contact requires the unembedded front path reference"
        )
    return ArchiveNode(
        RuntimeClass("moWireContact_c", 1),
        {
            "f50": MakeSweepRows(),
            "f90": 0.0,
            "f98": 0,
            "fa0": None,
            "fa8": 1.0,
            "fb0": 0,
            "fb8": 1,
            "fc8": -1,
            "fcc": 2,
            "fe0": None,
            "f40": 0,
            "f44": 0,
            "f48": 0,
            "fc0": -1.0,
            "fe8": PathValue,
        },
    )

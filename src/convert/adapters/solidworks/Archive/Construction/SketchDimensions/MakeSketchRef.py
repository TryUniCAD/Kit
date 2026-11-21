from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLocalRef import (
    MakeLocalRef,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a sketch dimension handle must reference the shared sketch and planned value group index rather than a feature dimension pointer
def MakeSketchRef(
    GraphValue: ProfileGraph, ValueNodes: tuple[ArchiveNode, ...], IndexValue: int
) -> ArchiveNode:
    FieldsValue = MakeLocalRef(19000)
    FieldsValue.update(
        {
            "owner": GraphValue.ProfileValue,
            "_values": ValueNodes,
            "has_f120": 0,
            "has_f128": 0,
            "f130": None,
            "f138": None,
            "f140": None,
            "f148": None,
            "f150": 0,
            "fe8": None,
            "f100": None,
            "f154": -1,
            "f118": 0,
            "ff0": GraphValue.GeometryValue.SketchValue,
            "ff8": IndexValue,
        }
    )
    return ArchiveNode(RuntimeClass("moSkDimHandleValG2_c", 1), FieldsValue)

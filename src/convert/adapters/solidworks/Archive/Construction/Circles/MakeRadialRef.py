from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.NeedCircle import (
    NeedCircle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLocalRef import (
    MakeLocalRef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# radial display ownership uses the actual local sketch and its value group index
def MakeRadialRef(GraphValue: ProfileGraph, DimensionValue: ArchiveNode) -> ArchiveNode:
    SketchValue = NeedCircle(GraphValue).SketchValue
    if (
        DimensionValue.ClassValue != RuntimeClass("sgCircleDim", 1)
        or DimensionValue.FieldsValue.get("_sketch") is not SketchValue
    ):
        raise ValueError("radial reference requires its actual local circle dimension")
    FieldsValue = MakeLocalRef(19000)
    FieldsValue.update(
        {
            "owner": GraphValue.ProfileValue,
            "_values": (DimensionValue,),
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
            "ff0": SketchValue,
            "ff8": 0,
        }
    )
    return ArchiveNode(RuntimeClass("moSkDimHandleRadial_c", 1), FieldsValue)

from math import hypot as NormValue, isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from interchange.geometry.Models.VectorSpace import SpaceVector


# the live note position needs an independently owned anchor and the authored displacement in the sheet frame
def SetNotePointMut(
    DisplayValue: ArchiveNode, DataValue: ArchiveNode, Position: SpaceVector
) -> None:
    Distance = NormValue(Position.x, Position.y, Position.z)
    if not IsFinite(Distance):
        raise ValueError("note displacement exceeds finite native geometry")
    if Distance:
        DisplayValue.FieldsValue["f628"] = MakePoint(
            XValue=Position.x / Distance,
            YValue=Position.y / Distance,
            ZValue=Position.z / Distance,
        )
    PointValue = ArchiveNode(
        RuntimeClass("moAbsolutePoint_c", 1),
        {
            "f08": MakePoint(),
            "f28": MakePoint(),
            "f20": 0,
            "f50": None,
            "f58": MakePoint(),
            "f70": MakePoint(),
            "f88": 0,
        },
    )
    CacheValue = ArchiveNode(
        RuntimeClass("moAttachPointData_c", 1),
        {
            "f08": MakePoint(),
            "f20": MakePoint(),
            "f38": None,
            "f40": 0.0,
            "f48": 0.0,
        },
    )
    DataValue.FieldsValue["f58"] = {"n": 1, "items": ({"o": PointValue},)}
    DisplayValue.FieldsValue.update(
        has_f298=1, f298={"n": 1, "items": ({"o": CacheValue},)}, f630=Distance
    )

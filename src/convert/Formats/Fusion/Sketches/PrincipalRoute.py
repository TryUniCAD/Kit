from convert.Formats.Fusion.Extrudes.Plane.OffsetBackend import KOffsetBackend
from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf


# variable parameter and child lists precede the reciprocal controller reference
def SketchRouteIds(FeatureBody: bytes) -> tuple[int, int]:
    Cursor = MetaCursor(FeatureBody)
    Cursor.Offset = 3
    ParamIds = tuple(ReadNativeRef(Cursor) for _ in range(Cursor.ReadCount(1024)))
    if (
        len(set(ParamIds)) != len(ParamIds)
        or Cursor.TakeBytes(1) not in (b"\0", b"\1")
        or Cursor.ReadWord()
    ):
        raise ValueError(
            "Unsupported Fusion principal sketch parameter or mesh section"
        )
    _ = ReadNativeRef(Cursor)
    ControllerId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(12) != bytes(12):
        raise ValueError("Unsupported Fusion sketch projection or surface dependency")
    _ = Cursor.ReadText(True, Maximum=1024)
    if Cursor.TakeBytes(3) != bytes(3):
        raise ValueError("Unsupported Fusion principal sketch feature flags")
    Count = Cursor.ReadCount(1026)
    Children = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if (
        Count != len(ParamIds) + 2
        or len(set(Children)) != Count
        or Children[1] != ControllerId
    ):
        raise ValueError("Fusion principal sketch controller copies disagree")
    return ControllerId, Children[0]


# placement alone cannot distinguish origin plane attachment from a coincident face
def PrincipalRoute(
    BulkData: bytes, Owners: dict[int, RecordSpan], Feature: RecordSpan
) -> tuple[int, int, int, int]:
    FeatureBody = BulkData[Feature.PayloadOffset + 4 : Feature.EndOffset]
    ControllerId, DescriptorId = SketchRouteIds(FeatureBody)
    Controller = SelectCursor(BulkData, Owners, ControllerId, KOffsetBackend)
    ControllerSize = len(Controller.DataValue)
    if ControllerSize not in (187, 315):
        raise ValueError("Unsupported Fusion principal sketch controller extent")
    Controller.Offset = ControllerSize - 103
    if Controller.ReadWord() != 1 or ReadNativeRef(Controller) != DescriptorId:
        raise ValueError("Fusion principal sketch descriptor copies disagree")
    Controller.Offset = ControllerSize - 11
    if ReadNativeRef(Controller) != Feature.ObjectId:
        raise ValueError("Fusion principal sketch controller owner disagrees")
    LeafId = ReadDescLeaf(BulkData, Owners, DescriptorId, Feature.ObjectId)
    return ControllerId, DescriptorId, LeafId, ReadEntityLeaf(BulkData, Owners, LeafId)

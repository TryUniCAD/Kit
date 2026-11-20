from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Maps.FindObject import FindObject
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag


# an inline backlink must resolve the same frame object without allocating a new body
def ReadFrameOwner(FrameValue: ReadFrame) -> ArchiveNode:
    ReaderValue = FrameValue.ReaderValue
    Cursor = ReaderValue.Cursor
    TagValue, Offset = ReadTag(Cursor.BytesValue, Cursor.OffsetValue)
    if TagValue.KindValue != "ObjectRef" or TagValue.IndexValue is None:
        raise BodyUnsupported("SOLIDWORKS component owner requires an existing object")
    OwnerValue = FindObject(ReaderValue.MapValue, TagValue.IndexValue)
    if OwnerValue is not FrameValue.NodeValue:
        raise BodyUnsupported(
            "SOLIDWORKS component owner differs from its enclosing part"
        )
    Cursor.OffsetValue = Offset
    return FrameValue.NodeValue

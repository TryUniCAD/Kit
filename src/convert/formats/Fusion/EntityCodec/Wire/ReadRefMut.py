from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def ReadRefMut(Cursor: MetaCursor) -> LocalRef | SegmentRef | None:
    if not ReadAtomMut(Cursor, WireType("bool")):
        return None
    ObjectId = Cursor.ReadLong()
    if ReadAtomMut(Cursor, WireType("bool")):
        raise ValueError("Cross-asset Fusion entity references are unsupported")
    if ReadAtomMut(Cursor, WireType("bool")):
        return SegmentRef(ObjectId, Cursor.ReadWord())
    return LocalRef(ObjectId)

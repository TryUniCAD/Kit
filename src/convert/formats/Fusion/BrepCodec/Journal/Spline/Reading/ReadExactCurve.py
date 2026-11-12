from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.ExactCurve import ExactCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadJumpsMut import (
    ReadJumpsMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadNubsCurve import (
    ReadNubsCurve,
)

KNullSupports = ("null_surface", "null_surface", "nullbs", "nullbs")


def ReadExactCurve(Cursor: FieldCursor) -> ExactCurve:
    Revision = ReadLongMut(Cursor)
    if Revision <= 0:
        raise ValueError("Unsupported Fusion exact curve serializer form")
    NeedFieldMut(Cursor, (21, 0))
    Cache = ReadNubsCurve(Cursor, 3)
    FitTolerance = ReadDoubleMut(Cursor)
    for Support in KNullSupports:
        NeedFieldMut(Cursor, (13, Support))
    CacheBounds = (ReadBoundMut(Cursor), ReadBoundMut(Cursor))
    Jumps = ReadJumpsMut(Cursor, 3)
    Extension = ReadLongMut(Cursor)
    Ranges = (ReadBoundMut(Cursor), ReadBoundMut(Cursor))
    TailCodes = (ReadLongMut(Cursor, 21), ReadLongMut(Cursor, 21))
    NeedFieldMut(Cursor, (16, None))
    return ExactCurve(
        Revision, Cache, FitTolerance, CacheBounds, Jumps, Extension, Ranges, TailCodes
    )

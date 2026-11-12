from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.ParCurve import ParCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadNubsCurve import (
    ReadNubsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadSurfScope import (
    ReadSurfScope,
)


def ReadParCurve(Cursor: FieldCursor) -> ParCurve:
    Cache = ReadNubsCurve(Cursor, 2)
    FitTolerance = ReadDoubleMut(Cursor)
    NeedFieldMut(Cursor, (13, "spline"))
    SupportFlag = IsLogicalMut(Cursor)
    Support = ReadSurfScope(Cursor)
    Bounds = (
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
    )
    NeedFieldMut(Cursor, (16, None))
    return ParCurve(Cache, FitTolerance, SupportFlag, Support, Bounds)

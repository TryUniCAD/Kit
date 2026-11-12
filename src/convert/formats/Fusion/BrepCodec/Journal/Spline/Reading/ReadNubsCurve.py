from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsCurve import NubsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.CountPoles import (
    CountPoles,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadKnotsMut import (
    ReadKnotsMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPointsMut import (
    ReadPointsMut,
)


def ReadNubsCurve(Cursor: FieldCursor, Width: int) -> NubsCurve:
    NeedFieldMut(Cursor, (13, "nubs"))
    Degree = ReadLongMut(Cursor)
    Closure = ReadLongMut(Cursor, 21)
    Knots = ReadKnotsMut(Cursor, ReadCountMut(Cursor, 1024))
    Points = ReadPointsMut(Cursor, CountPoles(Knots, Degree), Width)
    return NubsCurve(Degree, Closure, Knots, Points)

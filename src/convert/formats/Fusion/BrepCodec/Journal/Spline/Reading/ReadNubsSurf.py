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
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.CountPoles import (
    CountPoles,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadKnotsMut import (
    ReadKnotsMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPointsMut import (
    ReadPointsMut,
)


def ReadNubsSurf(Cursor: FieldCursor) -> NubsSurface:
    NeedFieldMut(Cursor, (13, "nubs"))
    DegreeU = ReadLongMut(Cursor)
    DegreeV = ReadLongMut(Cursor)
    Shape = tuple(ReadLongMut(Cursor, 21) for _ in range(4))
    CountU = ReadCountMut(Cursor, 1024)
    CountV = ReadCountMut(Cursor, 1024)
    KnotsU = ReadKnotsMut(Cursor, CountU)
    KnotsV = ReadKnotsMut(Cursor, CountV)
    Total = CountPoles(KnotsU, DegreeU) * CountPoles(KnotsV, DegreeV)
    if Total > 65536:
        raise ValueError("Fusion spline surface control net exceeds its quota")
    Points = tuple(
        (Entry[0], Entry[1], Entry[2]) for Entry in ReadPointsMut(Cursor, Total, 3)
    )
    return NubsSurface(
        DegreeU, DegreeV, Shape[0], Shape[1], Shape[2], Shape[3], KnotsU, KnotsV, Points
    )

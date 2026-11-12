from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadExactCurve import (
    ReadExactCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadScopeMut import (
    ReadScopeMut,
)


def ReadIntcurve(Cursor: FieldCursor) -> IntcurveNode:
    Prefix = ReadPrefixMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    if ReadScopeMut(Cursor) != "exact_int_cur":
        raise ValueError("Unsupported Fusion intcurve subtype")
    Curve = ReadExactCurve(Cursor)
    Lower = ReadBoundMut(Cursor)
    Upper = ReadBoundMut(Cursor)
    return IntcurveNode(Prefix, Reversed, Curve, Lower, Upper)

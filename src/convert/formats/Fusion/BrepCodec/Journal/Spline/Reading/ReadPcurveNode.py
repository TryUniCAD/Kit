from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadParCurve import (
    ReadParCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadScopeMut import (
    ReadScopeMut,
)


def ReadPcurveNode(Cursor: FieldCursor) -> PcurveNode:
    Prefix = ReadPrefixMut(Cursor)
    NeedFieldMut(Cursor, (4, 0))
    Reversed = IsLogicalMut(Cursor)
    if ReadScopeMut(Cursor) != "exp_par_cur":
        raise ValueError("Unsupported Fusion pcurve subtype")
    Curve = ReadParCurve(Cursor)
    OffsetU = ReadDoubleMut(Cursor)
    OffsetV = ReadDoubleMut(Cursor)
    return PcurveNode(Prefix, Reversed, Curve, OffsetU, OffsetV)

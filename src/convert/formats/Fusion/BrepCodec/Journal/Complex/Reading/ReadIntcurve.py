from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.ReadRuleMut import (
    ReadScopeMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.IntcurveNode import (
    IntcurveNode,
)
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


def ReadIntcurve(Cursor: FieldCursor) -> IntcurveNode:
    Prefix = ReadPrefixMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    Curve = ReadScopeMut(Cursor, "curve")
    Lower = ReadBoundMut(Cursor)
    Upper = ReadBoundMut(Cursor)
    return IntcurveNode(Prefix, Reversed, Curve, Lower, Upper)

from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadScopeMut import (
    ReadScopeMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadTsplSurf import (
    ReadTsplSurf,
)


def ReadSurfScope(Cursor: FieldCursor) -> TsplineSurf | SubtypeRef:
    Scope = ReadScopeMut(Cursor)
    if isinstance(Scope, SubtypeRef):
        return Scope
    if Scope != "t_spl_sur":
        raise ValueError("Unsupported Fusion spline surface subtype")
    return ReadTsplSurf(Cursor)

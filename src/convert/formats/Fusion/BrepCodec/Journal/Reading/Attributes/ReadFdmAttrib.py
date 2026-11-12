from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
    KFeatureLayouts,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)


def ReadFdmAttrib(Cursor: FieldCursor, Links: AttribLinks) -> FeatureAttrib:
    NeedFieldMut(Cursor, (4, 2))
    NeedFieldMut(Cursor, (4, 2))
    DataName = ReadTextMut(Cursor)
    if DataName not in KFeatureLayouts:
        raise ValueError("Unsupported Fusion feature attribute data")
    NeedFieldMut(Cursor, (4, 3))
    FeatureTag = ReadLongMut(Cursor)
    Flags = ReadLongMut(Cursor)
    NeedFieldMut(Cursor, (4, KFeatureLayouts[DataName]))
    TypeCode = ReadLongMut(Cursor)
    if DataName == "feature_data":
        return FeatureAttrib(Links, DataName, FeatureTag, Flags, TypeCode)
    Points = tuple(ReadVectorMut(Cursor, 19) for _ in range(3))
    return FeatureAttrib(
        Links, DataName, FeatureTag, Flags, TypeCode, Points, ReadLongMut(Cursor)
    )

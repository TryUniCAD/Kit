from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KHeaderLayout,
    KHeaderWords,
)
from convert.adapters.solidworks.Archive.Header.ReadHeaderBounds import ReadBoundsMut
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut


# explicit field order keeps metadata and nested objects on one archive cursor
def ReadWireFields(
    ReaderValue: GraphReader, LayoutValue: KHeaderLayout
) -> dict[str, object]:
    Cursor = ReaderValue.Cursor
    Fields: dict[str, object] = {}
    for FieldName, WireName in LayoutValue:
        Scalar = KHeaderWords.get(WireName)
        if Scalar is not None:
            Fields[FieldName] = int(Scalar.unpack(Cursor.TakeBytes(Scalar.size))[0])
        elif WireName == "text":
            Fields[FieldName] = ReadCStringMut(Cursor)
        elif WireName == "bounds":
            Fields[FieldName] = ReadBoundsMut(Cursor)
        elif WireName == "null":
            if ReadNodeMut(ReaderValue) is not None:
                raise ValueError("unsupported SOLIDWORKS header configuration object")
            Fields[FieldName] = None
        else:
            Fields[FieldName] = ReadTypedMut(ReaderValue, WireName, AllowNull=True)
    return Fields

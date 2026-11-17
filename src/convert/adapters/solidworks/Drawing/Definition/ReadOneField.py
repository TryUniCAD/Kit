from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeCount import ReadCountMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadTextMut
from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ReadScalarMut import ReadScalarMut


# ordinary field vocabulary shares the native cursor text count and object readers
def ReadOneField(Scope: FieldScope, KindName: str) -> object:
    Cursor = Scope.Reader.Cursor
    if KindName == "object":
        return ReadNodeMut(Scope.Reader)
    if KindName == "text":
        return ReadTextMut(Cursor)
    if KindName == "count":
        return ReadCountMut(Cursor, 1)
    return ReadScalarMut(Cursor, KindName)

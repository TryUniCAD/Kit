from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# unavailable visual property rows must fail at their own signed count
def ReadMatVizMut(Cursor: BinaryReader) -> dict[str, object]:
    BodyCount = ReadScalarMut(Cursor, "i32")
    if BodyCount != 0:
        raise BodyUnsupported("populated SOLIDWORKS body visual records")
    PropertyCount = ReadScalarMut(Cursor, "i32")
    if PropertyCount != 0:
        raise BodyUnsupported("populated SOLIDWORKS body visual properties")
    return {"n08": BodyCount, "bodies": [], "n58": PropertyCount, "props": []}

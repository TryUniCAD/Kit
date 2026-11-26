from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar
from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords


# bounded header cursors must retain their existing truncation checks before scalar decoding
def ReadScalarMut(Cursor: BinaryReader, KindName: str) -> int | float:
    DataValue = Cursor.TakeBytes(KScalarWords[KindName].size)
    NumberValue, _ = ReadScalar(DataValue, 0, KindName)
    return NumberValue

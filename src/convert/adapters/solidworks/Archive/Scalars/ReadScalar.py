from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords


# successful scalar decoding alone determines the next position of the caller cursor
def ReadScalar(
    BufferValue: bytes, OffsetValue: int, KindName: str
) -> tuple[int | float, int]:
    ScalarWord = KScalarWords[KindName]
    NumberValue = CastValue(
        int | float, ScalarWord.unpack_from(BufferValue, OffsetValue)[0]
    )
    return NumberValue, OffsetValue + ScalarWord.size

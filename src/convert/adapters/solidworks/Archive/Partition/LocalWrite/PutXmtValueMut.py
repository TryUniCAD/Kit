from math import isfinite as IsFinite
from struct import pack as PackValue
from types import MappingProxyType
from typing import cast as CastValue

from convert.Geometry.Parasolid import WritePointerMut
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalLimit,
)

# scalar domains require separate bounds for logical indices and signed values
KXmtIntegerCodes = MappingProxyType(
    {
        "l": (">B", 0, 1),
        "u": (">B", 0, (1 << 8) - 1),
        "w": (">H", 0, (1 << 16) - 1),
        "d": (">i", -(1 << 31), (1 << 31) - 1),
    }
)


# typed cells must reach canonical native encodings without numeric coercion
def PutXmtValueMut(
    OutputValue: bytearray, EncodingValue: str, MemberValue: object
) -> None:
    if EncodingValue == "p":
        if type(MemberValue) is not int or not 0 <= MemberValue <= KLocalLimit:
            raise ValueError(
                "local kernel pointer is outside the resident index domain"
            )
        WritePointerMut(OutputValue, MemberValue)
    elif EncodingValue == "c":
        if type(MemberValue) is not str or not MemberValue.isascii():
            raise ValueError("local kernel text requires ASCII characters")
        OutputValue.extend(MemberValue.encode("ascii"))
    elif EncodingValue in ("f", "v"):
        MembersValue = (
            CastValue(tuple[object, ...], MemberValue)
            if EncodingValue == "v" and type(MemberValue) is tuple
            else (MemberValue,)
        )
        if len(MembersValue) != (3 if EncodingValue == "v" else 1) or any(
            type(ItemValue) is not float or not IsFinite(ItemValue)
            for ItemValue in MembersValue
        ):
            raise ValueError("local kernel geometry requires finite scalar values")
        OutputValue.extend(
            PackValue(">ddd" if EncodingValue == "v" else ">d", *MembersValue)
        )
    else:
        IntegerCode = KXmtIntegerCodes.get(EncodingValue)
        if IntegerCode is None:
            raise ValueError("local kernel scalar encoding is unqualified")
        FormatText, LowerValue, UpperValue = IntegerCode
        if type(MemberValue) is not int or not LowerValue <= MemberValue <= UpperValue:
            raise ValueError("local kernel integer is outside its encoding domain")
        OutputValue.extend(PackValue(FormatText, MemberValue))

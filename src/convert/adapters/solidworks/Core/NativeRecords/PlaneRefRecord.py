from struct import Struct as RecordStruct

from convert.adapters.solidworks.Container.Container import SldprtFormatError

# the reference version identifies the current serialized handle layout
KHandleVersion = (19000).to_bytes(4, "little")

# the handle carries a persistent plane id and its creation time before the axis kind
KHandleFields = RecordStruct("<I4xHIB")

# explicit frame storage is optional for the identity basis
KMatrixSize = RecordStruct("<9d").size

# the frame tail distinguishes principal support from other transform states
KFrameTail = RecordStruct("<4dB")


# the bounded search keeps separate references from claiming the same sketch support
def FindPlaneRef(
    DataValue: bytes, Start: int, EndValue: int, PlaneIds: frozenset[int]
) -> tuple[int, int, int] | None:
    if Start < 0 or not PlaneIds:
        return None
    Limit = min(EndValue, len(DataValue))
    Cursor = Start
    Match = None
    while Cursor < Limit:
        Offset = DataValue.find(KHandleVersion, Cursor, Limit)
        if Offset < 0:
            break
        Cursor = Offset + len(KHandleVersion)
        Candidate = MatchPlaneRef(DataValue, Cursor, Limit, PlaneIds)
        if Candidate is None:
            continue
        if Match is not None:
            raise SldprtFormatError("ambiguous SOLIDWORKS principal plane references")
        Match = Candidate
    return Match


# the record layout ties candidate ownership to a complete principal support frame
def MatchPlaneRef(
    DataValue: bytes, Offset: int, EndValue: int, PlaneIds: frozenset[int]
) -> tuple[int, int, int] | None:
    FrameStart = Offset + KHandleFields.size
    if FrameStart > EndValue:
        return None
    PlaneId, OptionalRef, AxisKind, MatrixFlag = KHandleFields.unpack_from(
        DataValue, Offset
    )
    if (
        PlaneId not in PlaneIds
        or OptionalRef != 0
        or AxisKind not in (1, 2, 3)
        or MatrixFlag not in (0, 1)
    ):
        return None
    TailOffset = FrameStart + MatrixFlag * KMatrixSize
    if TailOffset + KFrameTail.size > EndValue:
        return None
    if KFrameTail.unpack_from(DataValue, TailOffset) != (0.0, 0.0, 0.0, 1.0, 0):
        return None
    return (Offset, PlaneId, AxisKind)

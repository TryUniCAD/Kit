from __future__ import annotations

from dataclasses import dataclass
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.container.Format import CLASS_MARKER as KClassMarker
from convert.adapters.solidworks.core.Native import ClassDecl, ReadClass

# the units table ends where the unit component begins
KUnitsEnd = "moUnitComponent_c"

# the sheet ends where the reference plane begins
KSheetEnd = "moRefPlane_c"

# the view ends where the sketch block manager begins
KViewEnd = "moSketchBlockMgr_c"

# the line styles end where the line font manager begins
KStyleEnd = "uiLineFontMgr_c"


# callers need the class name and its raw value bytes as one value
@dataclass(frozen=True, slots=True)
class ObjectBlock:
    ClassName: str
    Values: bytes


# the next declaration is needed because the value block has no length prefix
def NextClass(DataValue: bytes, Offset: int) -> int:
    Cursor = Offset
    while Cursor < len(DataValue) - 6:
        if DataValue[Cursor : Cursor + 4] == KClassMarker:
            (Length,) = Struct.unpack_from("<H", DataValue, Cursor + 4)
            NameValue = DataValue[Cursor + 6 : Cursor + 6 + Length]
            if 3 <= Length <= 40 and all(
                32 <= ItemValue < 127 for ItemValue in NameValue
            ):
                return Cursor
        Cursor += 1
    return -1


# the end class is needed because the object group has no length prefix
def ObjectBlocks(
    DataValue: bytes, StartClass: str, EndClass: str
) -> tuple[ObjectBlock, ...]:
    Start = DataValue.find(ClassDecl(StartClass))
    if Start < 0:
        raise SldprtFormatError(f"drawing definition has no {StartClass}")
    EndOffset = DataValue.find(ClassDecl(EndClass), Start)
    if EndOffset < 0:
        raise SldprtFormatError(f"drawing definition has no {EndClass}")
    Result: list[ObjectBlock] = []
    Offset = Start
    while Offset < EndOffset:
        ClassName, After = ReadClass(DataValue, Offset)
        NextOffset = NextClass(DataValue, After)
        if NextOffset < 0 or NextOffset > EndOffset:
            NextOffset = EndOffset
        Result.append(ObjectBlock(ClassName, DataValue[After:NextOffset]))
        Offset = NextOffset
    return tuple(Result)


# the writer needs the exact declaration and value layout to keep the stream valid
def EncodeBlocks(Blocks: tuple[ObjectBlock, ...]) -> bytes:
    Output = bytearray()
    for Block in Blocks:
        Output.extend(ClassDecl(Block.ClassName))
        Output.extend(Block.Values)
    return bytes(Output)

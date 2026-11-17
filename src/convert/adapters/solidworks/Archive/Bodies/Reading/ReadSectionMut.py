from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# model sections must prove their declared boundary instead of retaining an opaque body span
def ReadSectionMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    ByteCount = CastValue(int, ReadScalarMut(Cursor, "u32"))
    StartValue = Cursor.OffsetValue
    if ByteCount > Cursor.GetRemaining():
        raise ValueError("SOLIDWORKS model section exceeds its remaining stream")
    FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
    if Cursor.OffsetValue - StartValue != ByteCount:
        raise ValueError(
            f"SOLIDWORKS model section {RuleValue.MaskValue} has an incorrect length"
        )

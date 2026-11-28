from convert.Geometry.ParaFraming import KWrapperMagic
from convert.Geometry.ReadParaSection import ReadEmptyFrame

# the measured section and two ghost sheets have fixed class and resident counts
KSwFrameLimit = 32768


# the picked sweep transport owns one complete canonical compressed frame
def ReadSwFrame(WrappedValue: bytes) -> bytes:
    OffsetValue = 4 + len(KWrapperMagic)
    SizeValue = int.from_bytes(WrappedValue[OffsetValue : OffsetValue + 4], "little")
    if not 0 < SizeValue <= KSwFrameLimit or len(WrappedValue) > KSwFrameLimit:
        raise ValueError("SOLIDWORKS sweep transmit body exceeds its qualified extent")
    SectionValue = ReadEmptyFrame(WrappedValue, 0, SizeValue)
    if SectionValue is None or SectionValue.End != len(WrappedValue):
        raise ValueError("SOLIDWORKS sweep requires its complete single frame")
    return SectionValue.Data

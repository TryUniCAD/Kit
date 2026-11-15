from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import PutHandleMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutTextsMut import PutTextsMut
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import (
    KHeaderFill,
    KHeaderFinish,
    KHeaderStart,
    FrameParts,
    HasHighWord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderSpec import KHeaderSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.HeaderChecksum import (
    HeaderChecksum,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.TailCipher import EncryptBytes
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordSinks import RecordSinks
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.WalkSpec import (
    CachedSpec,
    PutWalkMut,
)

KProductCode = 1
KTailBitCount = 4 * 18
KVersionCodes = {"AC1027": 26, "AC1032": 26}


def EncodeTail(CipherValue: bytes) -> int:
    TextValue = "".join(
        "00" + format(CipherValue[Index], "08b") + format(CipherValue[Index + 1], "08b")
        for Index in range(0, len(CipherValue), 2)
    )
    return int(TextValue, 2)


def EmitHeaderVars(
    HeaderVars: DwgRecord, Frame: DwgRecord, FileHeader: DwgFileHeader
) -> bytes:
    Sinks = RecordSinks(FileHeader.VersionText)
    Writer = Sinks.DataWriter
    PutWalkMut(CachedSpec(KHeaderSpec), HeaderVars, Sinks, ())
    PutTextsMut(Writer, tuple(Sinks.TextItems), True)
    BitSize = Writer.BitCount + 32
    for Reference in Sinks.HandleRefs:
        PutHandleMut(Writer, Reference)
    EndBit = Writer.BitCount + 32
    AreaPrefix = PackFields("<I", BitSize) + Writer.ToBytes()
    ChecksumValue = HeaderChecksum(AreaPrefix, EndBit)
    VersionCode = KVersionCodes.get(FileHeader.VersionText)
    if VersionCode is None:
        raise ValueError("DWG header tail needs an encoded product code")
    TailPlain = PackFields("<HHHH", ChecksumValue, KProductCode, VersionCode, 0)
    Writer.PutBits(EncodeTail(EncryptBytes(TailPlain)), KTailBitCount)
    Padding = -Writer.BitCount & 7
    Writer.PutBits(KHeaderFill & ((1 << Padding) - 1), Padding)
    AreaValue = PackFields("<I", BitSize) + Writer.ToBytes()
    _, _, TrailBytes = FrameParts(Frame)
    HighWord = bytes(4) if HasHighWord(FileHeader) else b""
    Covered = PackFields("<I", len(AreaValue)) + HighWord + AreaValue
    CrcValue = PackFields("<H", CrcSixteen(0xC0C1, Covered))
    return KHeaderStart + Covered + CrcValue + KHeaderFinish + TrailBytes

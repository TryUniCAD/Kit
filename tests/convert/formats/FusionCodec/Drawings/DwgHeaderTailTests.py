from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import (
    FrameParts,
    KHeaderName,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.ReadHeaderVars import (
    LocateArea,
    TypeHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadInventory
from tests.convert.formats.FusionCodec.Drawings.DwgAuthorTests import (
    KViews,
    MakeDraft,
)


def Authored() -> tuple[bytes, DwgFile]:
    Content = AuthorDwg(MakeDraft(KViews))
    return Content, ReadDwgFile(Content)


def HeaderBytes(Content: bytes) -> bytes:
    Inventory = ReadInventory(Content)
    return next(
        Section.DataValue
        for Section in Inventory.Sections
        if Section.SectionInfo.SectionName == KHeaderName
    )


def Repaired(DataValue: bytearray, AreaFinish: int) -> bytes:
    DataValue[AreaFinish : AreaFinish + 2] = PackFields(
        "<H", CrcSixteen(0xC0C1, bytes(DataValue[16:AreaFinish]))
    )
    return bytes(DataValue)


def FlipTail(DataValue: bytes, Model: DwgFile) -> bytes:
    Width, _, _ = FrameParts(dict(Model.SectionVars)[KHeaderName])
    _, AreaFinish = LocateArea(DataValue, Model.FileHeader)
    FirstTailBit = AreaFinish * 8 - Width
    Offset = FirstTailBit // 8
    DataValue = bytearray(DataValue)
    DataValue[Offset] ^= 1 << (7 - FirstTailBit % 8)
    return Repaired(DataValue, AreaFinish)


def TestAuthoredTailTypes() -> None:
    Content, Model = Authored()
    DataValue = HeaderBytes(Content)
    Width, TailBits, _ = FrameParts(dict(Model.SectionVars)[KHeaderName])
    assert Width >= 72
    assert TailBits >> 72 == 0
    HeaderVars, Frames = TypeHeader(DataValue, Model.FileHeader)
    assert HeaderVars.RecordFields
    assert dict(Frames)[KHeaderName] == dict(Model.SectionVars)[KHeaderName]


def TestTailCrcRepairTypes() -> None:
    Content, Model = Authored()
    DataValue = HeaderBytes(Content)
    _, AreaFinish = LocateArea(DataValue, Model.FileHeader)
    HeaderVars, Frames = TypeHeader(
        Repaired(bytearray(DataValue), AreaFinish), Model.FileHeader
    )
    assert HeaderVars.RecordFields
    assert Frames


def TestTamperedChecksumRejects() -> None:
    Content, Model = Authored()
    DataValue = HeaderBytes(Content)
    Tampered = FlipTail(DataValue, Model)
    HeaderVars, Frames = TypeHeader(Tampered, Model.FileHeader)
    assert HeaderVars.RecordFields == ()
    assert Frames == ()

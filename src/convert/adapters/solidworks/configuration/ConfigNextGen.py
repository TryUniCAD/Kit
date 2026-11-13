from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass
import struct as Struct

from convert.adapters.solidworks.container.Archive import encode_string as EncodeString
from convert.adapters.solidworks.container.Cmgr import KDefaultRenderStyle
from convert.adapters.solidworks.container.CmgrNextGen import EncodeDSP
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.configuration.default.Program import (
    EncodeProgram as EncodeBaseProgram,
)

KGeneration = 19000
KConfigBytes = 25476
KIdentityBytes = 41
KReferenceNameWidth = 10
KVisualStart = 108
KVisualEnd = 729
KVisualFlagOffsets = (697, 705)
KReferenceBuild = 2026306


@Dataclass(frozen=True, slots=True)
class Addition:
    offset: int
    payload: bytes


def CheckedInsert(Buffer: bytes, Position: int, Payload: bytes) -> bytes:
    if Position < 0 or Position > len(Buffer):
        raise SldprtFormatError("Config-0 insertion point is outside the stream")
    return Buffer[:Position] + Payload + Buffer[Position:]


def EncodeSfTail() -> bytes:
    return EncodeString("") + EncodeString("") + Struct.pack("<II", 0, 0)


def ModernVisual() -> bytes:
    Payload = bytearray(
        EncodeDSP(101, KGeneration, KReferenceBuild, KDefaultRenderStyle)
    )
    del Payload[-KIdentityBytes:]
    Struct.pack_into("<I", Payload, KVisualFlagOffsets[0], 1)
    Struct.pack_into("<I", Payload, KVisualFlagOffsets[1], 0)
    return bytes(Payload)


def ValidateInputs(
    Atoms: tuple[tuple[int, int], ...],
    DualLengthUnits: bool,
    ViewCount: int,
    ParentTree: int | None,
    Variant: str,
) -> None:
    if len(Atoms) != 1:
        raise SldprtFormatError("Config-0 2026 currently requires one feature atom")
    if not DualLengthUnits:
        raise SldprtFormatError("Config-0 2026 requires dual length units")
    if ViewCount != 1 or ParentTree is not None or Variant != "default":
        raise SldprtFormatError("Config-0 2026 currently requires one annotation view")


def ApplyAdditions(Buffer: bytes, NameWidth: int) -> bytes:
    HelperTail = EncodeSfTail()
    PlaneTail = Struct.pack("<4I", 1, 1, 120, 1)
    Shift = (
        NameWidth
        - KReferenceNameWidth
        + len(ModernVisual())
        - (KVisualEnd - KVisualStart)
    )
    Records = (
        Addition(19470, Struct.pack("<I", 0)),
        Addition(17690, HelperTail),
        Addition(17384, HelperTail),
        Addition(16271, HelperTail),
        Addition(2600, PlaneTail),
    )
    for Record in Records:
        Buffer = CheckedInsert(Buffer, Record.offset + Shift, Record.payload)
    return Buffer


def UpdateGen(Buffer: bytes) -> bytes:
    Marker = Struct.pack("<III", 18000, 10000, 0x10000000)
    Position = Buffer.find(Marker)
    if Position < 0 or Buffer.find(Marker, Position + 1) >= 0:
        raise SldprtFormatError("Config-0 atom generation field could not be located")
    OutputData = bytearray(Buffer)
    Struct.pack_into("<III", OutputData, Position, KGeneration, 10000, 0x10000000)
    return bytes(OutputData)


def BuildNVConfig(
    PartName: str,
    Atoms: tuple[tuple[int, int], ...],
    SessionStamp: int,
    DualLengthUnits: bool,
    HighWater: tuple[int, int] | None,
    ViewCount: int,
    ParentTree: int | None,
    Variant: str,
) -> bytes:
    ValidateInputs(Atoms, DualLengthUnits, ViewCount, ParentTree, Variant)
    from convert.adapters.solidworks.configuration.ConfigZero import GetHighWater

    ResolvedWater = GetHighWater(Atoms, HighWater)
    Buffer = EncodeBaseProgram(
        PartName=PartName,
        Atoms=Atoms,
        SessionStamp=SessionStamp,
        Generation=18000,
        DualLengthUnits=DualLengthUnits,
        HighWater=ResolvedWater,
    )
    Shift = len(PartName.encode("utf-16le")) - KReferenceNameWidth
    Buffer = Buffer[:KVisualStart] + ModernVisual() + Buffer[KVisualEnd + Shift :]
    Buffer = ApplyAdditions(Buffer, len(PartName.encode("utf-16le")))
    Buffer = UpdateGen(Buffer)
    if len(Buffer) != KConfigBytes:
        raise SldprtFormatError("Config-0 2026 stream length is not the recovered size")
    return Buffer

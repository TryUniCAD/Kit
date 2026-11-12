from struct import unpack_from as UnpackFrom
from zlib import crc32 as CrcValue

from convert.formats.Fusion.ContainerCodec.ContainerLayout import (
    KMaxPreviewSide,
    KMaxPreviewSize,
)


def CheckPreview(Payload: bytes) -> None:
    if (
        type(Payload) is not bytes
        or not 57 <= len(Payload) <= KMaxPreviewSize
        or not Payload.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise ValueError("Invalid Fusion PNG preview")
    Offset = 8
    HasData = False
    ChunkCount = 0
    while Offset + 12 <= len(Payload):
        Length = int(UnpackFrom(">I", Payload, Offset)[0])
        Finish = Offset + 12 + Length
        KindValue = Payload[Offset + 4 : Offset + 8]
        ChunkCount += 1
        if Finish > len(Payload) or ChunkCount > 4096 or not KindValue.isalpha():
            raise ValueError("Invalid Fusion PNG preview chunk")
        Checksum = int(UnpackFrom(">I", Payload, Finish - 4)[0])
        if CrcValue(Payload[Offset + 4 : Finish - 4]) != Checksum:
            raise ValueError("Fusion PNG preview checksum disagrees")
        if Offset == 8:
            if KindValue != b"IHDR" or Length != 13:
                raise ValueError("Missing Fusion PNG preview header")
            Width, Height = UnpackFrom(">2I", Payload, Offset + 8)
            if not 0 < Width <= KMaxPreviewSide or not 0 < Height <= KMaxPreviewSide:
                raise ValueError("Oversized Fusion PNG preview dimensions")
        elif KindValue == b"IHDR":
            raise ValueError("Duplicate Fusion PNG preview header")
        if KindValue == b"IDAT":
            HasData = True
        if KindValue == b"IEND":
            if Length or Finish != len(Payload) or not HasData:
                raise ValueError("Invalid Fusion PNG preview termination")
            return
        Offset = Finish
    raise ValueError("Truncated Fusion PNG preview")

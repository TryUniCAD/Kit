# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import unpack_from as UnpackFrom
from zlib import crc32 as Checksum
from convert.adapters.solidworks.container.InflateStream import InflateStream
from convert.adapters.solidworks.container.RotateBytes import RotateBytes
from convert.adapters.solidworks.container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.container.StreamRecord import StreamRecord
from convert.adapters.solidworks.container.StreamLimits import (
    KMaxNameBytes,
    KMaxUncompressedStream,
)


def DecodeScanned(
    BlobValue: bytes,
    Offset: int,
    Signature: bytes,
    SizeLimit: int = KMaxUncompressedStream,
) -> StreamRecord | None:
    HeaderOffset = Offset + len(Signature)
    if HeaderOffset + 16 > len(BlobValue):
        return None
    CrcThreeTwoValue, CompressedSize, UncompressedSize, NameSize = UnpackFrom(
        "<IIII", BlobValue, HeaderOffset
    )
    if not 0 < NameSize <= KMaxNameBytes:
        return None
    NameOffset = HeaderOffset + 16
    PayloadOffset = NameOffset + NameSize
    PayloadEnd = PayloadOffset + CompressedSize
    if PayloadOffset > len(BlobValue):
        return None
    try:
        NameValue = RotateBytes(
            BlobValue[NameOffset:PayloadOffset], BlobValue[7]
        ).decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not NameValue or any((ord(Character) < 32 for Character in NameValue)):
        return None
    if (
        UncompressedSize > 0
        and CrcThreeTwoValue == (UncompressedSize * 2) & 4294967295
        and CompressedSize == UncompressedSize // 2
    ):
        return None
    if UncompressedSize > SizeLimit:
        raise SldprtFormat(f"SLDPRT decoded size limit exceeded by {NameValue!r}")
    if PayloadEnd > len(BlobValue):
        raise SldprtFormat(f"truncated SLDPRT stream {NameValue!r}")
    DataValue = InflateStream(BlobValue[PayloadOffset:PayloadEnd], UncompressedSize)
    if DataValue is None:
        raise SldprtFormat(f"invalid compressed SLDPRT stream {NameValue!r}")
    if Checksum(DataValue) & 4294967295 != CrcThreeTwoValue:
        raise SldprtFormat(f"SLDPRT checksum mismatch for {NameValue!r}")
    return StreamRecord(
        name=NameValue,
        data=DataValue,
        offset=Offset,
        payload_offset=PayloadOffset,
        compressed_size=CompressedSize,
        uncompressed_size=UncompressedSize,
        crc32=CrcThreeTwoValue,
        signature=Signature,
    )

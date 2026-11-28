import struct as Struct

# this binding exists because shared behavior needs one stable value
KLocalSignaturePrefix = bytes.fromhex("140006000800")


# local framing is calculated independently of the compressor implementation
def EncodeLocalHead(
    EncodedBytes: bytes,
    TypeId: int,
    CrcThreeTwoValue: int,
    CompressedSize: int,
    SizeValue: int,
) -> bytes:
    return b"".join(
        (
            KLocalSignaturePrefix,
            Struct.pack("<I", TypeId),
            Struct.pack(
                "<IIIHH",
                CrcThreeTwoValue,
                CompressedSize,
                SizeValue,
                len(EncodedBytes),
                0,
            ),
            EncodedBytes,
        )
    )

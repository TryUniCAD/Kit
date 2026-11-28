from convert.adapters.solidworks.Container.CheckArcTail import CheckArcTail, KFrameError
from convert.adapters.solidworks.Container.EncodeLocalHead import EncodeLocalHead
from convert.adapters.solidworks.Container.Container import (
    EncodedName,
    KArchiveOffset,
    KDefaultTypeId,
    KDirectoryRow,
    KTypeIdsByName,
    Signature,
    SldprtArchive,
)


# source attestation must account for every non deflate byte even when inspection scans for streams
def CheckArcFrames(BlobValue: bytes, Archive: SldprtArchive) -> None:
    Signatures = Signature(Archive.file_id)
    if Signatures is None:
        raise ValueError(KFrameError)
    Local, Central, EndBytes = Signatures
    VersionValue = Archive.format_version
    Cursor = KArchiveOffset
    Directory: list[KDirectoryRow] = []
    for Record in Archive.records:
        NameValue = Record.name
        TypeId = KTypeIdsByName.get(NameValue, KDefaultTypeId)
        Checksum, CompressedSize, SizeValue = (
            Record.crc32,
            Record.compressed_size,
            Record.uncompressed_size,
        )
        Header = Local + EncodeLocalHead(
            EncodedName(NameValue, VersionValue),
            TypeId,
            Checksum,
            CompressedSize,
            SizeValue,
        )
        if Record.payload_offset != Cursor + len(Header) or not BlobValue.startswith(
            Header, Cursor
        ):
            raise ValueError(KFrameError)
        Directory.append(
            (
                TypeId,
                NameValue,
                Checksum,
                CompressedSize,
                SizeValue,
                Cursor - KArchiveOffset,
            )
        )
        Cursor = Record.payload_offset + CompressedSize
    CheckArcTail(BlobValue, Directory, Cursor, Central, EndBytes, VersionValue)

from convert.adapters.solidworks.Container.Container import (
    EncodeArcEnd,
    EncodeFolder,
    EncodeLocalHead,
    KArchiveOffset,
    KDefaultTypeId,
    KDirectoryRow,
    KTypeIdsByName,
    Signature,
    SldprtArchive,
)

# the framing diagnostic stays specific to the source container being verified
KFrameError = "SLDPRT source container framing differs from its generated part"


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
            NameValue, TypeId, Checksum, CompressedSize, SizeValue, VersionValue
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


# the directory must cover the complete file and describe the same local records
def CheckArcTail(
    BlobValue: bytes,
    Directory: list[KDirectoryRow],
    Start: int,
    Central: bytes,
    EndBytes: bytes,
    VersionValue: int,
) -> None:
    Cursor = Start
    for Record in Directory:
        Entry = EncodeFolder(*Record, Central, VersionValue)
        if not BlobValue.startswith(Entry, Cursor):
            raise ValueError(KFrameError)
        Cursor += len(Entry)
    Trailer = EncodeArcEnd(
        EndBytes, len(Directory), Cursor - Start, Start - KArchiveOffset
    )
    if len(BlobValue) != Cursor + len(Trailer) or not BlobValue.startswith(
        Trailer, Cursor
    ):
        raise ValueError(KFrameError)

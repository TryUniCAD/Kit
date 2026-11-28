from convert.adapters.solidworks.Container.Container import (
    EncodeFolder,
    KArchiveOffset,
    KDirectoryRow,
)
from convert.adapters.solidworks.Container.EncodeArcEnd import EncodeArcEnd

# the framing diagnostic stays specific to the source container being verified
KFrameError = "SLDPRT source container framing differs from its generated part"


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

from functools import partial as BindArgs
from json import loads as LoadJson
from pathlib import Path as FilePath
from zipfile import ZipFile as ArchiveFile


# the object hook marks cited bytes directly without reconstructing the reported gaps
def MarkCitedMut(
    Coverage: dict[str, bytearray], Fields: dict[str, object]
) -> dict[str, object]:
    if Fields.get("$type") != "ProvenanceSpan":
        return Fields
    StreamName, StartPos, SpanSize = (
        Fields.get("stream"),
        Fields.get("offset"),
        Fields.get("length"),
    )
    if (
        isinstance(StreamName, str)
        and StreamName in Coverage
        and type(StartPos) is int
        and type(SpanSize) is int
    ):
        EndPos = StartPos + SpanSize
        if 0 <= StartPos < EndPos <= len(Coverage[StreamName]):
            Coverage[StreamName][StartPos:EndPos] = b"\x01" * SpanSize
    return Fields


# each known member must be covered by disjoint cited bytes and maximal reported gaps
def VerifyFileGaps(
    SourcePath: FilePath,
    PartialPath: FilePath,
    MemberSizes: dict[str, int],
    Ranges: list[list[object]],
) -> None:
    with ArchiveFile(SourcePath) as Archive:
        Coverage = {
            Member.filename: bytearray(Member.file_size)
            for Member in Archive.infolist()
        }
    assert MemberSizes == {
        StreamName: len(MemberBytes) for StreamName, MemberBytes in Coverage.items()
    }
    _ = LoadJson(PartialPath.read_bytes(), object_hook=BindArgs(MarkCitedMut, Coverage))
    for StreamName, StartPos, EndPos in Ranges:
        assert (
            isinstance(StreamName, str)
            and type(StartPos) is int
            and type(EndPos) is int
        )
        MemberBytes = Coverage[StreamName]
        assert 0 <= StartPos < EndPos <= len(MemberBytes)
        assert StartPos == 0 or MemberBytes[StartPos - 1] == 1
        assert EndPos == len(MemberBytes) or MemberBytes[EndPos] == 1
        assert not any(MemberBytes[StartPos:EndPos])
        MemberBytes[StartPos:EndPos] = b"\x02" * (EndPos - StartPos)
    assert all(all(MemberBytes) for MemberBytes in Coverage.values())
    assert sum(MemberBytes.count(1) for MemberBytes in Coverage.values()) == 11067

from functools import partial as BindArgs
from json import loads as LoadJson
from pathlib import Path as FilePath
from zipfile import ZipFile as ArchiveFile

from tests.CliResearch.Reports.ScopeSpanEvidence import MarkCitedMut


# each known member must be covered by disjoint cited bytes and maximal reported gaps
def VerifyFileGaps(
    SourcePath: FilePath,
    PartialPath: FilePath,
    MemberSizes: list[tuple[str, int]],
    Ranges: list[list[object]],
) -> None:
    with ArchiveFile(SourcePath) as Archive:
        RawMembers = Archive.infolist()
    Coverage = {Member.filename: bytearray(Member.file_size) for Member in RawMembers}
    assert len(RawMembers) == len(Coverage) == len(MemberSizes)
    assert dict(MemberSizes) == {
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

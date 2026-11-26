from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.ArchiveValues.RunBodyValues import RunBodyValues


# counted rows must retain depth and map ownership for every linked object
def TestCountDepth(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Counted.json"
    WirePath = TmpPath / "Counted.bin"
    ReadPath = TmpPath / "Read.json"
    _ = SourcePath.write_text(
        DumpJson({"depth": 128, "counted": True}), encoding="utf-8"
    )
    WriteResult = RunBodyValues("write", SourcePath, WirePath)
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert WirePath.read_bytes() == (
        PackValues("<HHH", 0xFFFF, 1, 8)
        + b"RowDepth"
        + PackValues("<HH", 2, 0x8001) * 127
        + PackValues("<HHH", 2, 2, 0)
        + PackValues("<H", 0) * 127
    )
    ReadResult = RunBodyValues("read", WirePath, ReadPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(ReadPath.read_text(encoding="utf-8")) == {
        "depth": 128,
        "terminal_index": 2,
    }

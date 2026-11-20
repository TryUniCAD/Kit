from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveValues.MakeValueWire import (
    KChildLabel,
    MakeValueWire,
)
from tests.Convert.Solidworks.ArchiveValues.RunBodyValues import RunBodyValues


# unrelated processes must agree on scalar text and shared object rows
def TestBodyValues(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Authored.json"
    WirePath = TmpPath / "Values.bin"
    ReadPath = TmpPath / "Read.json"
    Label = "\u03bb\U00010437"
    AuthoredValue = {"number": -29, "label": Label, "child_label": KChildLabel}
    _ = SourcePath.write_text(DumpJson(AuthoredValue), encoding="utf-8")
    WriteResult = RunBodyValues("write", SourcePath, WirePath)
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert WirePath.read_bytes() == MakeValueWire(
        b"\xff\xfe\xff\x03" + Label.encode("utf-16-le")
    )
    ReadResult = RunBodyValues("read", WirePath, ReadPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(ReadPath.read_text(encoding="utf-8")) == {
        **AuthoredValue,
        "row_count": 3,
        "root_index": 2,
        "child_index": 4,
    }


# canonical ansi keeps its source representation across separate processes
def TestAnsiValues(TmpPath: FilePath) -> None:
    NativePath = TmpPath / "Ansi.bin"
    ReadPath = TmpPath / "Read.json"
    ReplayPath = TmpPath / "Replay.bin"
    SourceBytes = MakeValueWire(b"\x02\xe9\xff")
    _ = NativePath.write_bytes(SourceBytes)
    ReadResult = RunBodyValues("read", NativePath, ReadPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(ReadPath.read_text(encoding="utf-8"))["label"] == ["A", "\xe9\xff"]
    ReplayResult = RunBodyValues("write", ReadPath, ReplayPath)
    assert ReplayResult.returncode == 0, ReplayResult.stdout + ReplayResult.stderr
    assert ReplayPath.read_bytes() == SourceBytes

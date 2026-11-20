from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.ArchiveValues.RunBodyValues import RunBodyValues


# the writer can terminate its deepest body with a backreference and null
def TestValueDepth(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Depth.json"
    WirePath = TmpPath / "Depth.bin"
    ReadPath = TmpPath / "Read.json"
    _ = SourcePath.write_text(DumpJson({"depth": 128}), encoding="utf-8")
    WriteResult = RunBodyValues("write", SourcePath, WirePath)
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert WirePath.read_bytes() == (
        PackValues("<HHH", 0xFFFF, 1, 5)
        + b"Depth"
        + PackValues("<H", 0x8001) * 127
        + PackValues("<HH", 2, 0)
        + PackValues("<H", 0) * 127
    )
    ReadResult = RunBodyValues("read", WirePath, ReadPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(ReadPath.read_text(encoding="utf-8")) == {
        "depth": 128,
        "terminal_index": 2,
    }


# any attempted extra body or empty descriptor must prevent publication
def TestWriteReject(TmpPath: FilePath) -> None:
    for LabelName, InputValue, ErrorText in (
        (
            "ReusedClass",
            {"depth": 129},
            "SOLIDWORKS body nesting exceeds the supported depth",
        ),
        (
            "NewClass",
            {"depth": 129, "new_terminal_class": True},
            "SOLIDWORKS body nesting exceeds the supported depth",
        ),
        (
            "CountedClass",
            {"depth": 129, "counted": True, "new_terminal_class": True},
            "SOLIDWORKS body nesting exceeds the supported depth",
        ),
        (
            "EmptyClass",
            {"class": "", "number": -29, "label": "a", "child_label": "b"},
            "SOLIDWORKS archive class name must not be empty",
        ),
    ):
        SourcePath = TmpPath / f"{LabelName}.json"
        WirePath = TmpPath / f"{LabelName}.bin"
        _ = SourcePath.write_text(DumpJson(InputValue), encoding="utf-8")
        ResultValue = RunBodyValues("write", SourcePath, WirePath)
        assert ResultValue.returncode != 0
        assert ErrorText in ResultValue.stderr
        assert not WirePath.exists()

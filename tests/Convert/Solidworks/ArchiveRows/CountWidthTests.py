from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.ArchiveRows.RunRows import RunRows


# an explicit vendor count and an inline framework count both retain accepted widths
def TestCountWidths(TmpPath: FilePath) -> None:
    NativePath = TmpPath / "Escaped.bin"
    ReadPath = TmpPath / "Read.json"
    ReplayPath = TmpPath / "Replay.bin"
    SourceBytes = PackValues(
        "<HIiHIQiiIIII", 0xFFFF, 1, -9, 0xFFFF, 0xFFFFFFFF, 1, 11, -7, 3, 0, 0, 0
    )
    _ = NativePath.write_bytes(SourceBytes)
    ReadResult = RunRows("read", NativePath, ReadPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    ModelValue = LoadJson(ReadPath.read_text(encoding="utf-8"))
    assert ModelValue["row_count"] == ModelValue["framework_rows#count"] == 1
    assert ModelValue["row_count#width"] == 6
    assert ModelValue["framework_rows#count#width"] == 14
    assert (ModelValue["split_high"], ModelValue["split_low"]) == (3, 0)
    ReplayResult = RunRows("write", ReadPath, ReplayPath)
    assert ReplayResult.returncode == 0, ReplayResult.stdout + ReplayResult.stderr
    assert ReplayPath.read_bytes() == SourceBytes
    ModelValue["rows"].append({"value": 21})
    ModelValue["framework_rows"].clear()
    ModelValue["split_rows"].append({"value": 8})
    EditedPath = TmpPath / "Edited.json"
    DerivedPath = TmpPath / "Derived.bin"
    _ = EditedPath.write_text(DumpJson(ModelValue), encoding="utf-8")
    EditedResult = RunRows("write", EditedPath, DerivedPath)
    assert EditedResult.returncode == 0, EditedResult.stdout + EditedResult.stderr
    assert DerivedPath.read_bytes() == PackValues(
        "<HiiHiIIiII", 2, -9, 21, 0, -7, 0, 1, 8, 0, 0
    )

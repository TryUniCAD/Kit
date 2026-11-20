from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Solidworks.ArchiveRows.RunRows import RunRows


# authored rows must drive counts while equivalent signed and split source words survive
def TestCountedRows(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Authored.json"
    WirePath = TmpPath / "Rows.bin"
    ReadPath = TmpPath / "Read.json"
    AuthoredValue = {
        "row_count": -1,
        "rows": [{"value": -11}, {"value": 21}],
        "framework_rows#count": 20_000_000,
        "framework_rows": [],
        "signed_count": -7,
        "signed_rows": [],
        "split_high": 7,
        "split_low": 1,
        "split_rows": [{"value": -17}],
        "combined_rows#count": 1,
        "combined_rows": [{"value": 31}],
    }
    _ = SourcePath.write_text(DumpJson(AuthoredValue), encoding="utf-8")
    WriteResult = RunRows("write", SourcePath, WirePath)
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert WirePath.read_bytes() == PackValues(
        "<HiiHiIIiIIi", 2, -11, 21, 0, -7, 7, 1, -17, 0, 1, 31
    )
    ReadResult = RunRows("read", WirePath, ReadPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(ReadPath.read_text(encoding="utf-8")) == {
        **AuthoredValue,
        "row_count": 2,
        "framework_rows#count": 0,
    }

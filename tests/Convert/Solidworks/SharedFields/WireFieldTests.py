from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.Archive.RunWire import RunWire


# transitions must not borrow bytes from neighboring mixed width fields
def TestWireFields(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Fields.json"
    WirePath = TmpPath / "Fields.bin"
    ReadPath = TmpPath / "Read.json"
    Fields = [
        {
            "tag": ["ObjectRef", 0x7FFFFFFF],
            "label": ["x" * 254 + "é", False],
            "vendor_count": 0xFFFF,
            "framework_count": 0x100000000,
            "rows": [
                [["ClassRef", 1], ["x" * 254, True], -1, 1.5, 2.0],
                [["ObjectRef", 0x7FFE], ["x" * 65533, True], 1, -1.5, -2.0],
            ],
        },
    ]
    _ = SourcePath.write_text(DumpJson(Fields), encoding="utf-8")
    WriteResult = RunWire("replay", SourcePath, WirePath)
    assert WriteResult.returncode == 0, WriteResult.stderr
    ReadResult = RunWire("read", WirePath, ReadPath)
    assert ReadResult.returncode == 0, ReadResult.stderr
    assert LoadJson(ReadPath.read_text(encoding="utf-8")) == Fields

from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.Archive.AnsiRecord import AnsiRecord
from tests.Convert.Solidworks.Archive.AnsiWire import AnsiWire
from tests.Convert.Solidworks.Archive.RunWire import RunWire


# the source replay gate must preserve ansi bytes while fresh text requires unicode
def TestAnsiWire(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Source.bin"
    DecodedPath = TmpPath / "Decoded.json"
    ReplayedPath = TmpPath / "Replayed.bin"
    FreshPath = TmpPath / "Fresh.bin"
    SourceValue = AnsiWire()
    _ = SourcePath.write_bytes(SourceValue)
    ReadResult = RunWire("read", SourcePath, DecodedPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(DecodedPath.read_text(encoding="utf-8")) == AnsiRecord()
    ReplayResult = RunWire("replay", DecodedPath, ReplayedPath)
    assert ReplayResult.returncode == 0, ReplayResult.stdout + ReplayResult.stderr
    assert ReplayedPath.read_bytes() == SourceValue
    FreshResult = RunWire("write", DecodedPath, FreshPath)
    assert FreshResult.returncode != 0
    assert "native wide string output requires Unicode text" in FreshResult.stderr
    assert not FreshPath.exists()

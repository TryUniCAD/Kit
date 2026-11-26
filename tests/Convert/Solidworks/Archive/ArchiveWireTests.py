from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.Archive.ArchiveWireCases import AuthoredRecord
from tests.Convert.Solidworks.Archive.BrokenWire import BrokenRecords
from tests.Convert.Solidworks.Archive.CanonicalWire import CanonicalWire
from tests.Convert.Solidworks.Archive.RunWire import RunWire


# neighboring wire fields reveal wrong widths even when individual values round trip
def TestArchiveWire(TmpPath: FilePath) -> None:
    AuthoredPath = TmpPath / "Authored.json"
    EncodedPath = TmpPath / "Encoded.bin"
    DecodedPath = TmpPath / "Decoded.json"
    AuthoredValue = AuthoredRecord()
    _ = AuthoredPath.write_text(DumpJson(AuthoredValue), encoding="utf-8")
    WriteResult = RunWire("write", AuthoredPath, EncodedPath)
    assert WriteResult.returncode == 0, WriteResult.stdout + WriteResult.stderr
    assert EncodedPath.read_bytes() == CanonicalWire()
    ReadResult = RunWire("read", EncodedPath, DecodedPath)
    assert ReadResult.returncode == 0, ReadResult.stdout + ReadResult.stderr
    assert LoadJson(DecodedPath.read_text(encoding="utf-8")) == AuthoredValue


# malformed framing must fail before any projected record is published
def TestBrokenWire(TmpPath: FilePath) -> None:
    for LabelName, PayloadValue, ExpectedError in BrokenRecords(CanonicalWire()):
        EncodedPath = TmpPath / f"{LabelName}.bin"
        DecodedPath = TmpPath / f"{LabelName}.json"
        _ = EncodedPath.write_bytes(PayloadValue)
        ReadResult = RunWire("read", EncodedPath, DecodedPath)
        assert ReadResult.returncode != 0
        assert ExpectedError in ReadResult.stderr
        assert not DecodedPath.exists()

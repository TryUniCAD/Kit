from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Archive.ArchiveWireCases import (
    AuthoredRecord,
    BrokenRecords,
    CanonicalWire,
)

# fresh interpreters must resolve the same repository even from temporary directories
KRepoRoot = FilePath(__file__).resolve().parents[4]


# a dedicated command exposes only synthetic records to the process integration
KWireScript = KRepoRoot / "re/tooling/sw2026/ArchiveWireProcess.py"


# a process boundary keeps the reader independent from the writer cursor and objects
def RunWire(
    ModeName: str, InputPath: FilePath, OutputPath: FilePath
) -> CompletedProcess[str]:
    return RunProcess(
        [PythonExec, "-B", str(KWireScript), ModeName, str(InputPath), str(OutputPath)],
        cwd=InputPath.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


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

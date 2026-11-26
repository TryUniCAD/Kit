from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from os import environ as Environment, pathsep as PathSep
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue


from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.FreeCadAliases.MakePadFixture import MakePadFixture

# child processes must load the same native decoder as the public registry
KRepoRoot = FilePath(__file__).resolve().parents[4]


# a fresh child observes the independently authored archive without importing test fixture internals
def ReadPadCase(TmpPath: FilePath, CaseName: str) -> CadDocument:
    SourcePath = TmpPath / "LocalSketch.FCStd"
    Payload = MakePadFixture(CaseName)
    assert SourcePath.write_bytes(Payload) == len(Payload)
    Process = RunProcess(
        [PythonExe, "-B", "-P", "-m", "tests.Research.Archives.FreeCadNativeEndTests"],
        cwd=TmpPath,
        env={
            **Environment,
            "PYTHONPATH": PathSep.join((str(KRepoRoot), str(KRepoRoot / "src"))),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    assert SourcePath.read_bytes() == Payload
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Report["input_sha256"] == DigestBytes(Payload).hexdigest()
    return CadDocument.from_json(EncodeJson(Report["document"]))

from __future__ import annotations

from base64 import b64decode as DecodeBytes
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import KAssemblyName


# projection must receive the physical bytes produced by the guarded native builder
def RunMateBundle(
    Request: dict[str, object], OutputDir: FilePath
) -> tuple[FilePath, FilePath]:
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/DistanceMateBundleProcess.py"),
        ],
        cwd=KRepoRoot,
        input=DumpJson(Request),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["input_runtime_file_access_attempts"] == 0
    assert Report["writer_output_count"] == 2 and Report["native_acceptance"] is False
    OutputDir.mkdir()
    ParentPath = OutputDir / (KAssemblyName + ".SLDASM")
    ChildPath = OutputDir / "GeneratedChildFile.SLDPRT"
    for RoleName, Target in (("assembly", ParentPath), ("child", ChildPath)):
        RowValue = CastValue(dict[str, object], Report[RoleName])
        BlobValue = DecodeBytes(
            CastValue(str, RowValue["artifact_base64"]), validate=True
        )
        assert len(BlobValue) == RowValue["bytes"]
        assert HashBytes(BlobValue).hexdigest() == RowValue["sha256"]
        assert Target.write_bytes(BlobValue) == len(BlobValue)
    return ParentPath, ChildPath

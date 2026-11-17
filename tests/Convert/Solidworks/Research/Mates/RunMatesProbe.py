from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# actual generated native bytes must reach a fresh interpreter before linked codec evidence is trusted
def RunMatesProbe(ParentPath: FilePath) -> dict[str, object]:
    BlobValue = ParentPath.read_bytes()
    Archive = SldprtArchive.from_bytes(BlobValue)
    Request = {
        "path": str(ParentPath),
        "sha256": HashBytes(BlobValue).hexdigest(),
        "bytes": len(BlobValue),
        "stream_sha256": HashBytes(
            Archive.require("Contents/Config-0-MatesList")
        ).hexdigest(),
    }
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/SdkMatesProcess.py"),
            "--worker",
            "--root",
            str(KRepoRoot),
        ],
        cwd=KRepoRoot,
        input=DumpJson(Request),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))

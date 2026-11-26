from json import dumps as WriteJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe

from tests.Research.Archives.BossIntent.Candidate.CandidateContext import MakeContext
from tests.Research.Archives.BossIntent.Candidate.CandidateProgram import (
    KRequestProgram,
)


# independent processes must consume only the request and explicitly authored constructor context
def RunCandidate(
    RequestPath: FilePath,
    Digest: str,
    CandidatePath: FilePath | None = None,
    *,
    PreserveKeywordOrder: bool = False,
) -> CompletedProcess[str]:
    RootPath = FilePath(__file__).resolve().parents[5]
    return RunProcess(
        [
            PythonExe,
            "-I",
            "-B",
            "-c",
            KRequestProgram,
            str(RootPath),
            str(RequestPath),
            Digest,
            str(CandidatePath) if CandidatePath is not None else "",
            "source" if PreserveKeywordOrder else "default",
        ],
        cwd=RootPath,
        input=WriteJson(MakeContext()),
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.CliResearch.ResearchRoot import ResearchRoot


# independent role replay must invoke the candidate emitter with only a typed document and its fixed generation options
def EmitFusionRole(InputPath: FilePath, LocatorValue: str, WrittenAt: int) -> bytes:
    ReplayPath = InputPath.parent
    OutputPath = ReplayPath / "Candidate.f3d"
    Result = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            "-c",
            """
from pathlib import Path as FilePath
from sys import argv as KArguments, path as KModulePath

# the independent caller supplies only the trusted checkout and durable writer inputs
KRootPath, KInputPath, KOutputPath, KLocator, KEpoch = KArguments[1:]

KModulePath[:0] = [
    str(FilePath(KRootPath) / Entry) for Entry in ('src', 're/automation')
]
from EncoderRoundTrip.Fusion import generate_prepared_candidate as EmitCandidate
from interchange.document.Models.DocumentModel import CadDocument

# typed reconstruction consumes the persisted constructor document as the sole model input
KDocument = CadDocument.from_json(FilePath(KInputPath).read_text(encoding='utf-8'))

# the location and epoch bind the constructor output to its recorded role
KPayload = EmitCandidate(KDocument, native_locator=KLocator, written_at=int(KEpoch))
FilePath(KOutputPath).write_bytes(KPayload)
""",
            str(ResearchRoot()),
            str(InputPath),
            str(OutputPath),
            LocatorValue,
            str(WrittenAt),
        ),
        cwd=ReplayPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env={**KEnvironment, "KIT_NATIVE_API_DIRECTORY": str(ReplayPath / "NativeApi")},
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    return OutputPath.read_bytes()

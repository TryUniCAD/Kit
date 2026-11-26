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
import sys
from pathlib import Path

root, input_path, output_path, locator, epoch = sys.argv[1:]
sys.path[:0] = [str(Path(root) / item) for item in ('src', 're/automation')]
from EncoderRoundTrip.Fusion import generate_prepared_candidate
from interchange import CadDocument

document = CadDocument.from_json(Path(input_path).read_text(encoding='utf-8'))
payload = generate_prepared_candidate(document, native_locator=locator, written_at=int(epoch))
Path(output_path).write_bytes(payload)
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

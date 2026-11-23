from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

# each public entry and refusal has its own fresh process
KProofModes = (
    "registry",
    "adapter",
    "no-receipt",
    "forged-disclosed",
    "wrong-body",
    "wrong-location",
    "strict-location",
    "foreign-heldout",
    "tampered-heldout",
)


# exact native evidence must bind both generated members through both public write routes
def TestPerpProof() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    ProbePath = RootPath / "re/tooling/sw2026/VerifyMeasuredPerp.py"
    for ModeValue in KProofModes:
        Outcome = RunProcess(
            (PythonExe, "-I", "-B", str(ProbePath), ModeValue),
            cwd=RootPath,
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )
        assert Outcome.returncode == 0, Outcome.stderr
        Report = LoadJson(Outcome.stdout)
        assert Report["passed"] is True
        assert Report["runtime_input_file_reads"] == Report["native_processes_started"] == 0
        if ModeValue in ("registry", "adapter"):
            assert Report["publications"] == 1 and Report["matching_streams"] == 22
            assert Report["readback"]["child_drivers"] == 3
            assert Report["readback"]["mate_endpoints"] == 2
        else:
            assert Report["publications"] == 0 and Report["refusals"] == 1

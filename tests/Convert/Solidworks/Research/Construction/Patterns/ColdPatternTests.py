from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# the normal strict reader must recover six generated geometry histories at the process boundary
def TestColdPatRead() -> None:
    Script = KRepoRoot / "re/tooling/sw2026/linear_pattern/ProveColdPatternRead.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Script), "--portable"),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
    Report: dict[str, object] = LoadJson(Outcome.stdout)
    assert Report["isolated_processes"] == 12
    assert Report["ordinary_path_and_stream_reads"] == 12
    assert Report["native_processes_started"] == Report["heldout_payloads_read"] == 0

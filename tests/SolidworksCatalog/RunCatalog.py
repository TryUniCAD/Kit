from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonPath


# subprocess boundaries verify catalogue tools without importing research code into tests
def RunCatalog(ToolName: str, *Arguments: str) -> CompletedProcess[str]:
    RepoRoot = FilePath(__file__).resolve().parents[2]
    ToolPath = RepoRoot / "re" / "solidworks" / "PlannerCatalog" / ToolName
    assert ToolPath.is_file(), "Catalogue entry point is missing"
    return RunProcess(
        [PythonPath, "-B", str(ToolPath), *Arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

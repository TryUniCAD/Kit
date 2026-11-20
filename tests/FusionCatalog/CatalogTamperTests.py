from pathlib import Path as FilePath
from shutil import copytree as CopyTree
from subprocess import run as RunProcess
from sys import executable as PythonPath


# changed export bytes must fail verification before a planner consumes a damaged bundle
def CheckTamperFail(TmpPath: FilePath) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[2]
    CatalogRoot = RepoRoot / "re" / "Fusion" / "PlannerCatalog"
    SourcePath = CatalogRoot / "Data"
    _ = CopyTree(SourcePath, TmpPath, dirs_exist_ok=True)
    _ = (TmpPath / "ApiTypes.csv").write_text("changed inventory\n")
    Result = RunProcess(
        [PythonPath, str(CatalogRoot / "VerifyCatalog.py"), str(TmpPath)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Result.returncode == 2
    assert "integrity mismatch: ApiTypes.csv" in Result.stderr

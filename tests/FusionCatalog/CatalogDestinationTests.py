from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath


# fresh destination enforcement protects previous inventories and other user owned files
def CheckFreshDest(TmpPath: FilePath) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[2]
    CatalogRoot = RepoRoot / "re" / "Fusion" / "PlannerCatalog"
    OwnerPath = TmpPath / "Owned.txt"
    OwnerPath.write_text("preserve this file\n")
    Result = RunProcess(
        [
            PythonPath,
            str(CatalogRoot / "BuildCatalog.py"),
            "--api-root",
            str(RepoRoot),
            "--output",
            str(TmpPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Result.returncode == 2 and "already exists" in Result.stderr
    assert OwnerPath.read_text() == "preserve this file\n"

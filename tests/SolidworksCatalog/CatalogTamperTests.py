from pathlib import Path as FilePath
from shutil import copytree as CopyTree

from tests.SolidworksCatalog.RunCatalog import RunCatalog


# altered exported records must fail verification before planners consume the bundle
def CheckTamper(TmpPath: FilePath) -> None:
    SavedRoot = (
        FilePath(__file__).resolve().parents[2]
        / "re"
        / "solidworks"
        / "PlannerCatalog"
        / "Data"
    )
    OutputPath = CopyTree(SavedRoot, TmpPath / "Tampered")
    ExportPath = OutputPath / "ApiTypes.csv"
    ExportPath.write_bytes(ExportPath.read_bytes() + b"unexpected,row\n")
    Result = RunCatalog("VerifyCatalog.py", str(OutputPath))
    assert Result.returncode != 0
    assert "Artifact fingerprint differs: ApiTypes.csv" in Result.stderr

from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from shutil import copytree as CopyTree

from tests.SolidworksCatalog.RunCatalog import RunCatalog


# manifest versions must remain bound to the observed installation provenance
def CheckVersion(TmpPath: FilePath) -> None:
    SavedRoot = (
        FilePath(__file__).resolve().parents[2]
        / "re"
        / "solidworks"
        / "PlannerCatalog"
        / "Data"
    )
    OutputPath = CopyTree(SavedRoot, TmpPath / "VersionTampered")
    ManifestPath = OutputPath / "Manifest.json"
    ManifestData = LoadJson(ManifestPath.read_text(encoding="utf-8"))
    ManifestData["application_version"] = "999.0.0.0"
    _ = ManifestPath.write_text(DumpJson(ManifestData), encoding="utf-8")
    Result = RunCatalog("VerifyCatalog.py", str(OutputPath))
    assert Result.returncode != 0
    assert "Application version differs from source provenance" in Result.stderr

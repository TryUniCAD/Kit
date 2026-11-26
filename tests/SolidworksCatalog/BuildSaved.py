from pathlib import Path as FilePath
from subprocess import CompletedProcess

from tests.SolidworksCatalog.RunCatalog import RunCatalog


# saved declaration inputs permit full regeneration on machines without the vendor installation
def BuildSaved(OutputPath: FilePath) -> CompletedProcess[str]:
    RepoRoot = FilePath(__file__).resolve().parents[2]
    SourceRoot = RepoRoot / "re" / "solidworks" / "PlannerCatalog" / "Sources"
    return RunCatalog(
        "BuildCatalog.py",
        "--api-snapshot",
        str(SourceRoot / "ApiSnapshot.json"),
        "--feature-plan",
        str(SourceRoot / "FeaturePlan.json"),
        "--output",
        str(OutputPath),
    )

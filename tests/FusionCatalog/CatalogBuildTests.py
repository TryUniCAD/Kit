from json import loads as LoadJson
from pathlib import Path as FilePath
from sqlite3 import connect as OpenSqlite
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.FusionCatalog.PrepareApi import PrepareApi


# real builder and verifier processes must produce usable fresh inventories without executing input definitions
def CheckBuildFlow(TmpPath: FilePath) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[2]
    CatalogRoot = RepoRoot / "re" / "Fusion" / "PlannerCatalog"
    ModuleRoot = PrepareApi(TmpPath)
    OutputRoot = TmpPath / "Fresh"
    Result = RunProcess(
        [
            PythonPath,
            str(CatalogRoot / "BuildCatalog.py"),
            "--api-root",
            str(ModuleRoot),
            "--research-root",
            str(RepoRoot),
            "--commands",
            str(CatalogRoot / "Sources" / "Commands.json"),
            "--output",
            str(OutputRoot),
            "--all-csv",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)["application_version"] == "fixture-only"
    Verified = RunProcess(
        [PythonPath, str(CatalogRoot / "VerifyCatalog.py"), str(OutputRoot)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Verified.returncode == 0, Verified.stderr
    assert (OutputRoot / "Items.csv").is_file()
    Database = OpenSqlite(
        (OutputRoot / "Catalog.sqlite").as_uri() + "?mode=ro", uri=True
    )
    try:
        assert Database.execute(
            "SELECT COUNT(*) FROM items WHERE source_id='commands:current' AND kind='ui_command'"
        ).fetchone() == (3151,)
        assert Database.execute(
            "SELECT COUNT(*) FROM gaps WHERE source_id='commands:current' AND code='ui_getter_unavailable'"
        ).fetchone() == (88,)
        assert Database.execute(
            "SELECT target_id FROM relations WHERE owner_id=? AND relation='property_type'",
            ("api:adsk.fusion.ProbeFeatureInput.mode",),
        ).fetchone() == ("api:adsk.fusion.ProbeMode",)
        assert Database.execute(
            "SELECT json_extract(details,'$.value') FROM items WHERE id=?",
            ("api:adsk.fusion.ProbeMode.Secondary",),
        ).fetchone() == (-1,)
    finally:
        Database.close()

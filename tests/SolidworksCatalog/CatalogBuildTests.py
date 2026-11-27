from json import loads as LoadJson
from pathlib import Path as FilePath
from sqlite3 import connect as OpenSqlite

from tests.SolidworksCatalog.BuildSaved import BuildSaved
from tests.SolidworksCatalog.RunCatalog import RunCatalog


# independent process regeneration must preserve every saved record and artifact digest
def CheckBuildFlow(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Fresh"
    Result = BuildSaved(OutputPath)
    assert Result.returncode == 0, Result.stderr
    Verified = RunCatalog("VerifyCatalog.py", str(OutputPath))
    assert Verified.returncode == 0, Verified.stderr
    SavedRoot = (
        FilePath(__file__).resolve().parents[2]
        / "re"
        / "solidworks"
        / "PlannerCatalog"
        / "Data"
    )
    FreshData = LoadJson((OutputPath / "Manifest.json").read_text())
    SavedData = LoadJson((SavedRoot / "Manifest.json").read_text())
    for FieldName in ("counts", "content_sha256", "source_sha256", "csv_exports"):
        assert FreshData[FieldName] == SavedData[FieldName]
    for FileName in FreshData["csv_exports"]:
        assert (OutputPath / FileName).read_bytes() == (
            SavedRoot / FileName
        ).read_bytes()
    with OpenSqlite(
        (OutputPath / "Catalog.sqlite").as_uri() + "?mode=ro", uri=True
    ) as Database:
        assert Database.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert not Database.execute("PRAGMA foreign_key_check").fetchall()
        assert Database.execute(
            "SELECT COUNT(*) FROM items WHERE authoring_status != 'unverified' OR decoding_status != 'unverified' OR writing_status != 'unverified' OR verification_status != 'unverified'"
        ).fetchone() == (0,)

from json import loads as LoadJson
from pathlib import Path as FilePath
from sqlite3 import connect as OpenSqlite
from subprocess import run as RunProcess
from sys import executable as PythonPath

# committed inventory artifacts must remain usable without the licensed application or api installation
KRepoRoot = FilePath(__file__).resolve().parents[2]


# process entry points exercise the actual catalogue verifier and database views together
KCatalogRoot = KRepoRoot / "re" / "Fusion" / "PlannerCatalog"


# published metadata must preserve editable options and unknown schemas without claiming qualification
def CheckBundleRead() -> None:
    Result = RunProcess(
        [
            PythonPath,
            str(KCatalogRoot / "VerifyCatalog.py"),
            str(KCatalogRoot / "Data"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Result.returncode == 0, Result.stderr
    Report = LoadJson(Result.stdout)
    assert Report["status"] == "verified_inventory"
    Database = OpenSqlite(
        (KCatalogRoot / "Data" / "Catalog.sqlite").as_uri() + "?mode=ro", uri=True
    )
    try:
        Property = Database.execute(
            "SELECT json_extract(details,'$.writable') FROM api_effective_members "
            "WHERE type_id=? AND name='operation' AND kind='api_property'",
            ("api:adsk.fusion.ExtrudeFeatureInput",),
        ).fetchone()
        assert Property == (1,)
        assert Database.execute(
            "SELECT json_extract(details,'$.availability_status'),json_extract(details,'$.retired'),"
            "json_extract(details,'$.documentation_mentions.retirement') "
            "FROM items WHERE id='api:adsk.fusion.Occurrence.transform2'"
        ).fetchone() == ("unverified", None, 1)
        assert Database.execute(
            "SELECT target_id FROM relations WHERE owner_id=? AND relation='property_type'",
            ("api:adsk.fusion.ExtrudeFeatureInput.operation",),
        ).fetchone() == ("api:adsk.fusion.FeatureOperations",)
        assert (
            Database.execute(
                "SELECT COUNT(*) FROM native_schemas WHERE lookup_status='uninitialized' AND member_count IS NULL"
            ).fetchone()[0]
            > 0
        )
        assert (
            Database.execute(
                "SELECT COUNT(*) FROM native_schemas WHERE lookup_status='initialized' AND member_count=0"
            ).fetchone()[0]
            > 0
        )
    finally:
        Database.close()

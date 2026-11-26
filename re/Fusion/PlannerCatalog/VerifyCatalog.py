from argparse import ArgumentParser
from collections import Counter
from csv import reader
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from sqlite3 import DatabaseError, connect

from CatalogDatabase import RecordDigest
from CatalogRows import CatalogRows


# independent readback checks published data without requiring the vendor installation or a live application
def VerifyCatalog(BundlePath):
    BundlePath = BundlePath.resolve(strict=True)
    Manifest = loads((BundlePath / "Manifest.json").read_bytes())
    if Manifest["schema"] != "FusionPlannerCatalog/1":
        raise ValueError("Unsupported catalogue schema")
    if not {
        "Catalog.sqlite",
        "ApiOptions.csv",
        "ApiEnums.csv",
        "ApiTypes.csv",
        "Commands.csv",
        "NativeTypes.csv",
        "Gaps.csv",
    }.issubset(Manifest["files"]):
        raise ValueError("Manifest is missing required catalogue files")
    for Name, Record in Manifest["files"].items():
        if Path(Name).name != Name or Name in (".", ".."):
            raise ValueError("Manifest filename escapes catalogue")
        SourcePath = BundlePath / Name
        if SourcePath.is_symlink():
            raise ValueError("Catalogue files must not be symlinks")
        Content = SourcePath.read_bytes()
        if (
            len(Content) != Record["size_bytes"]
            or sha256(Content).hexdigest() != Record["sha256"]
        ):
            raise ValueError("Catalogue file integrity mismatch: " + Name)
    Database = connect((BundlePath / "Catalog.sqlite").as_uri() + "?mode=ro", uri=True)
    try:
        if Database.execute("PRAGMA user_version").fetchone() != (1,):
            raise ValueError("Database schema version mismatch")
        Metadata = {
            Key: loads(Value)
            for Key, Value in Database.execute("SELECT key,value FROM metadata")
        }
        if any(
            Metadata[Key] != Manifest[Key]
            for Key in ("schema", "application_version", "content_sha256")
        ):
            raise ValueError("Manifest and database metadata disagree")
        if (
            Database.execute("PRAGMA integrity_check").fetchone() != ("ok",)
            or Database.execute("PRAGMA foreign_key_check").fetchall()
        ):
            raise ValueError("Database integrity failed")
        Rows = CatalogRows()
        for Query, Mapping in (
            (
                "SELECT id,kind,label,sha256,application_version,details FROM sources",
                Rows.Sources,
            ),
            ("SELECT id,kind,name,parent_id,source_id,details FROM items", Rows.Items),
            (
                "SELECT owner_id,target_id,relation,source_id,details FROM relations",
                Rows.Relations,
            ),
            ("SELECT id,code,item_id,source_id,details FROM gaps", Rows.Gaps),
        ):
            for Record in Database.execute(Query):
                Mapping[Record if Mapping is Rows.Relations else Record[0]] = Record
        Rows.Validate()
        if RecordDigest(Rows) != Manifest["content_sha256"]:
            raise ValueError("Canonical catalogue fingerprint mismatch")
        Counts = dict(sorted(Counter(Row[1] for Row in Rows.Items.values()).items()))
        GapCounts = dict(sorted(Counter(Row[1] for Row in Rows.Gaps.values()).items()))
        if Counts != Manifest["items"] or GapCounts != Manifest["gaps"]:
            raise ValueError("Manifest inventory counts mismatch")
        if (
            len(Rows.Sources) != Manifest["sources"]
            or len(Rows.Relations) != Manifest["relations"]
        ):
            raise ValueError("Manifest relationship or source count mismatch")
        if Database.execute(
            "SELECT COUNT(*) FROM items WHERE authoring_status!='unverified' OR decoding_status!='unverified' OR writing_status!='unverified' OR verification_status!='unverified'"
        ).fetchone() != (0,):
            raise ValueError(
                "Discovery catalogue contains unsupported qualification claims"
            )
        InvalidSchemas = Database.execute("""
            SELECT s.id FROM native_schemas s LEFT JOIN items m ON m.parent_id=s.id AND m.kind='native_member'
            GROUP BY s.id,s.lookup_status,s.member_count
            HAVING (s.lookup_status='initialized' AND (s.member_count IS NULL OR s.member_count!=COUNT(m.id)))
             OR (s.lookup_status!='initialized' AND (s.member_count IS NOT NULL OR COUNT(m.id)!=0))
        """).fetchall()
        if InvalidSchemas:
            raise ValueError("Unknown or initialized schema member counts disagree")
        CsvCounts = {
            "ApiOptions.csv": Counts.get("api_property", 0)
            + Counts.get("api_method", 0),
            "ApiEnums.csv": Counts.get("api_enum_value", 0)
            + Counts.get("api_constant", 0),
            "ApiTypes.csv": Counts.get("api_type", 0),
            "Commands.csv": Counts.get("ui_command", 0),
            "NativeTypes.csv": Counts.get("native_type", 0),
            "Gaps.csv": len(Rows.Gaps),
        }
        for Name, ExpectedCount in CsvCounts.items():
            with (BundlePath / Name).open(newline="", encoding="utf-8") as Stream:
                if sum(1 for Record in reader(Stream)) - 1 != ExpectedCount:
                    raise ValueError("CSV row count mismatch: " + Name)
        return {
            "status": "verified_inventory",
            "application_version": Manifest["application_version"],
            "content_sha256": Manifest["content_sha256"],
            "items": Counts,
            "gaps": GapCounts,
        }
    finally:
        Database.close()


# explicit verification gives planners a cheap acceptance check before consuming a bundle
def MainRun():
    Parser = ArgumentParser(
        description="Verify a Fusion planner catalogue without vendor software"
    )
    Parser.add_argument("catalog", type=Path)
    Arguments = Parser.parse_args()
    try:
        Result = VerifyCatalog(Arguments.catalog)
    except (OSError, ValueError, KeyError, TypeError, DatabaseError) as Error:
        Parser.exit(2, "Catalogue verification failed: " + str(Error) + "\n")
    print(dumps(Result, indent=2, sort_keys=True))


if __name__ == "__main__":
    MainRun()

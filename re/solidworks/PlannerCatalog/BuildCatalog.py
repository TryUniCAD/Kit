from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from shutil import rmtree
from sqlite3 import connect, sqlite_version
from tempfile import mkdtemp

from ApiInventory import AddApiMut
from CatalogDatabase import ReadSummary, WriteDatabase, WriteExport
from CatalogRows import CatalogRows, ReadInput
from CatalogSchema import KExports, KNotice
from PlanInventory import AddPlanMut
from VerifyCatalog import VerifyBundle


# atomic publication protects existing research evidence from partial collector failures
def BuildBundle(ApiPath, PlanPath, Output, AllCsv=False):
    Output = Output.resolve()
    if Output.exists():
        raise FileExistsError("Output directory already exists")
    ApiData, ApiDigest = ReadInput(ApiPath)
    PlanData, PlanDigest = ReadInput(PlanPath)
    Rows = CatalogRows()
    AddApiMut(Rows, ApiData, ApiDigest)
    AddPlanMut(Rows, PlanData, PlanDigest)
    Output.parent.mkdir(parents=True, exist_ok=True)
    Working = Path(mkdtemp(prefix="SolidworksCatalog", dir=Output.parent))
    try:
        WriteDatabase(Rows, Working / "Catalog.sqlite")
        Manifest = WriteBundle(Working, ApiDigest, PlanDigest, AllCsv)
        Manifest["_notice"] = KNotice
        Manifest["application_version"] = ApiData.get("collection", {}).get(
            "installation_version", "unobserved"
        )
        (Working / "Manifest.json").write_text(
            dumps(Manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        VerifyBundle(Working)
        Working.rename(Output)
    except BaseException:
        rmtree(Working)
        raise
    return Manifest


# every exported artifact is bound to both canonical records and source fingerprints
def WriteBundle(Working, ApiDigest, PlanDigest, AllCsv):
    Exports = dict(KExports)
    if AllCsv:
        Exports.update({"Sources.csv": "sources", "Items.csv": "items"})
    Database = connect((Working / "Catalog.sqlite").as_uri() + "?mode=ro", uri=True)
    try:
        Counts, Digest = ReadSummary(Database)
        CsvData = {
            Name: {"view": View, "rows": WriteExport(Database, View, Working / Name)}
            for Name, View in sorted(Exports.items())
        }
    finally:
        Database.close()
    Artifacts = {
        FilePath.name: {
            "sha256": sha256(FilePath.read_bytes()).hexdigest(),
            "bytes": FilePath.stat().st_size,
        }
        for FilePath in sorted(Working.iterdir())
    }
    return {
        "schema_version": 1,
        "sqlite_version": sqlite_version,
        "content_sha256": Digest,
        "source_sha256": {"api_snapshot": ApiDigest, "feature_plan": PlanDigest},
        "counts": Counts,
        "csv_exports": CsvData,
        "artifacts": Artifacts,
        "qualification": {
            "authoring": "unverified",
            "decoding": "unverified",
            "writing": "unverified",
            "verification": "unverified",
        },
    }


# explicit source arguments allow metadata rebuilds without a licensed cad installation
def ReadArgs():
    Parser = ArgumentParser(
        description="Build the SOLIDWORKS research planner catalogue"
    )
    Parser.add_argument("--api-snapshot", required=True, type=Path)
    Parser.add_argument("--feature-plan", required=True, type=Path)
    Parser.add_argument("--output", required=True, type=Path)
    Parser.add_argument("--all-csv", action="store_true")
    return Parser.parse_args()


# process output supplies bounded counts instead of exposing source paths or metadata dumps
def MainEntry():
    Args = ReadArgs()
    Result = BuildBundle(
        Args.api_snapshot, Args.feature_plan, Args.output, Args.all_csv
    )
    print(
        dumps(
            {"counts": Result["counts"], "content_sha256": Result["content_sha256"]},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    MainEntry()

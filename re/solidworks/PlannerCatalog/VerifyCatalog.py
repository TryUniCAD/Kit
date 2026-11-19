# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from csv import reader
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from sqlite3 import connect

from CatalogSchema import KSchema


# query interfaces are part of the planner contract rather than unverified convenience views
def CheckSchema(Database):
    Expected = connect(":memory:")
    try:
        Expected.executescript(KSchema)
        Query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if Database.execute(Query).fetchall() != Expected.execute(Query).fetchall():
            raise ValueError("Database schema or planner query views differ")
    finally:
        Expected.close()


# independent canonicalization prevents serializer bugs from blessing their own output
def CanonicalText(Value):
    return dumps(
        Value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


# artifact names must never escape the selected immutable bundle directory
def CheckArtifacts(RootPath, Manifest):
    Expected = set(Manifest["artifacts"]) | {"Manifest.json"}
    Actual = {Value.name for Value in RootPath.iterdir()}
    if Expected != Actual or "Catalog.sqlite" not in Expected:
        raise ValueError("Bundle artifact set differs from manifest")
    for Name, Details in Manifest["artifacts"].items():
        if (
            Path(Name).name != Name
            or Name in (".", "..")
            or not (Name == "Catalog.sqlite" or Name.endswith(".csv"))
        ):
            raise ValueError("Invalid artifact identity")
        FilePath = RootPath / Name
        if FilePath.is_symlink() or not FilePath.is_file():
            raise ValueError("Artifact must be a regular file")
        if (
            FilePath.stat().st_size != Details["bytes"]
            or sha256(FilePath.read_bytes()).hexdigest() != Details["sha256"]
        ):
            raise ValueError("Artifact fingerprint differs: " + Name)


# logical record verification remains meaningful across sqlite physical storage versions
def CheckRecords(Database, Manifest):
    Digest = sha256()
    Counts = {}
    for Table in ("sources", "items", "relations", "gaps"):
        Counts[Table] = 0
        Digest.update((Table + "\n").encode())
        for Record in Database.execute("SELECT * FROM " + Table + " ORDER BY id"):
            Digest.update((CanonicalText(Record) + "\n").encode())
            Counts[Table] += 1
    Counts["item_kinds"] = dict(
        Database.execute("SELECT kind,count(*) FROM items GROUP BY kind ORDER BY kind")
    )
    if Digest.hexdigest() != Manifest["content_sha256"] or Counts != Manifest["counts"]:
        raise ValueError("Canonical database contents differ")
    return Counts


# csv readback checks every exported field rather than only row counts
def CheckExports(Database, RootPath, Manifest):
    Required = {
        "ApiTypes.csv": "api_types",
        "ApiOptions.csv": "api_options",
        "ApiEnums.csv": "api_enums",
        "Commands.csv": "command_candidates",
        "Features.csv": "feature_plan",
        "Gaps.csv": "gaps",
        "Relations.csv": "relations",
        "NativeSchemas.csv": "native_schemas",
    }
    Optional = {"Sources.csv": "sources", "Items.csv": "items"}
    Exports = Manifest["csv_exports"]
    if not set(Required).issubset(Exports) or set(Exports) - set(Required) - set(
        Optional
    ):
        raise ValueError("Unexpected catalogue exports")
    for Name, Details in Exports.items():
        View = {**Required, **Optional}[Name]
        if Details["view"] != View:
            raise ValueError("Unexpected export source")
        Cursor = Database.execute("SELECT * FROM " + View + " ORDER BY id")
        with (RootPath / Name).open(encoding="utf-8", newline="") as Input:
            Records = reader(Input)
            if next(Records, None) != [Column[0] for Column in Cursor.description]:
                raise ValueError("CSV columns differ: " + Name)
            Count = 0
            for Row in Cursor:
                if next(Records, None) != [
                    "" if Value is None else str(Value) for Value in Row
                ]:
                    raise ValueError("CSV record differs: " + Name)
                Count += 1
            if next(Records, None) is not None or Count != Details["rows"]:
                raise ValueError("CSV row count differs: " + Name)


# planned and declared evidence cannot accidentally qualify implemented feature support
def CheckMeaning(Database, Manifest):
    SourceDetails = Database.execute(
        "SELECT details FROM sources WHERE id='source:api-snapshot'"
    ).fetchone()
    if not SourceDetails or Manifest.get("application_version") != loads(
        SourceDetails[0]
    ).get("installation_version", "unobserved"):
        raise ValueError("Application version differs from source provenance")
    if Manifest["qualification"] != dict.fromkeys(
        ("authoring", "decoding", "writing", "verification"), "unverified"
    ):
        raise ValueError("Inventory cannot qualify implementation support")
    if Database.execute(
        "SELECT count(*) FROM items WHERE authoring_status!='unverified' OR decoding_status!='unverified' OR writing_status!='unverified' OR verification_status!='unverified'"
    ).fetchone()[0]:
        raise ValueError("An inventory row incorrectly qualifies support")
    for Key, SourceId in (
        ("api_snapshot", "source:api-snapshot"),
        ("feature_plan", "source:feature-plan"),
    ):
        Record = Database.execute(
            "SELECT sha256 FROM sources WHERE id=?", (SourceId,)
        ).fetchone()
        if not Record or Record[0] != Manifest["source_sha256"][Key]:
            raise ValueError("Input provenance differs")
    if Database.execute("SELECT count(*) FROM native_schemas").fetchone()[0]:
        raise ValueError("COM declarations cannot establish native wire schemas")
    Required = {
        "availability_unverified",
        "native_wire_schema_unobserved",
        "command_registration_unobserved",
        "parameter_domains_unverified",
        "api_to_wire_mapping_unverified",
        "planning_domains_unverified",
    }
    Actual = {
        Record[0] for Record in Database.execute("SELECT DISTINCT code FROM gaps")
    }
    if not Required.issubset(Actual):
        raise ValueError("Required unresolved evidence is missing")


# inheritance and research dependencies must not produce impossible cyclic scheduling
def CheckCycles(Database):
    Edges = {}
    for Owner, Target in Database.execute(
        "SELECT owner_id,target_id FROM relations WHERE kind IN ('planned_dependency','inherits')"
    ):
        Edges.setdefault(Owner, set()).add(Target)
        Edges.setdefault(Target, set())
    Ready = [Owner for Owner, Targets in Edges.items() if not Targets]
    Reverse = {}
    for Owner, Targets in Edges.items():
        for Target in Targets:
            Reverse.setdefault(Target, set()).add(Owner)
    Visited = 0
    while Ready:
        Target = Ready.pop()
        Visited += 1
        for Owner in Reverse.get(Target, ()):
            Edges[Owner].remove(Target)
            if not Edges[Owner]:
                Ready.append(Owner)
    if Visited != len(Edges):
        raise ValueError("Catalogue dependencies contain a cycle")


# read only verification works without installed cad software or original source metadata
def VerifyBundle(RootPath):
    RootPath = RootPath.resolve(strict=True)
    Manifest = loads((RootPath / "Manifest.json").read_text(encoding="utf-8"))
    if Manifest.get("schema_version") != 1:
        raise ValueError("Unsupported catalogue schema")
    CheckArtifacts(RootPath, Manifest)
    Database = connect((RootPath / "Catalog.sqlite").as_uri() + "?mode=ro", uri=True)
    try:
        Database.execute("PRAGMA query_only=ON")
        CheckSchema(Database)
        if (
            Database.execute("PRAGMA user_version").fetchone()[0] != 1
            or Database.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
            or Database.execute("PRAGMA foreign_key_check").fetchall()
        ):
            raise ValueError("Database schema or integrity failed")
        Counts = CheckRecords(Database, Manifest)
        CheckExports(Database, RootPath, Manifest)
        CheckMeaning(Database, Manifest)
        CheckCycles(Database)
    finally:
        Database.close()
    return Counts


# bounded process receipts make automated readback useful without leaking local paths
def MainEntry():
    Parser = ArgumentParser(
        description="Verify the SOLIDWORKS research planner catalogue"
    )
    Parser.add_argument("bundle", type=Path)
    Args = Parser.parse_args()
    print(
        dumps({"verified": True, "counts": VerifyBundle(Args.bundle)}, sort_keys=True)
    )


if __name__ == "__main__":
    MainEntry()

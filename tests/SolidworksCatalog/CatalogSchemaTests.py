# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as ShaDigest
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from shutil import copytree as CopyTree
from sqlite3 import connect as OpenSqlite

from tests.SolidworksCatalog.RunCatalog import RunCatalog


# matching artifact hashes must never bless changed planner query semantics
def CheckSchemaData(TmpPath: FilePath) -> None:
    SavedRoot = (
        FilePath(__file__).resolve().parents[2]
        / "re"
        / "solidworks"
        / "PlannerCatalog"
        / "Data"
    )
    OutputPath = CopyTree(SavedRoot, TmpPath / "SchemaTampered")
    DatabasePath = OutputPath / "Catalog.sqlite"
    with OpenSqlite(DatabasePath) as Database:
        Database.execute("DROP VIEW api_feature_types")
        Database.execute("CREATE VIEW api_feature_types AS SELECT * FROM api_types")
    Database.close()
    ManifestPath = OutputPath / "Manifest.json"
    ManifestData = LoadJson(ManifestPath.read_text(encoding="utf-8"))
    ManifestData["artifacts"]["Catalog.sqlite"] = {
        "bytes": DatabasePath.stat().st_size,
        "sha256": ShaDigest(DatabasePath.read_bytes()).hexdigest(),
    }
    ManifestPath.write_text(DumpJson(ManifestData), encoding="utf-8")
    Result = RunCatalog("VerifyCatalog.py", str(OutputPath))
    assert Result.returncode != 0
    assert "Database schema or planner query views differ" in Result.stderr

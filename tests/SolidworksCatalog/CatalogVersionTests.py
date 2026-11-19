# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
    ManifestPath.write_text(DumpJson(ManifestData), encoding="utf-8")
    Result = RunCatalog("VerifyCatalog.py", str(OutputPath))
    assert Result.returncode != 0
    assert "version" in Result.stderr.lower()

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from shutil import copytree as CopyTree

from tests.SolidworksCatalog.RunCatalog import RunCatalog


# altered exported records must fail verification before planners consume the bundle
def CheckTamper(TmpPath: FilePath) -> None:
    SavedRoot = (
        FilePath(__file__).resolve().parents[2]
        / "re"
        / "solidworks"
        / "PlannerCatalog"
        / "Data"
    )
    OutputPath = CopyTree(SavedRoot, TmpPath / "Tampered")
    ExportPath = OutputPath / "ApiTypes.csv"
    ExportPath.write_bytes(ExportPath.read_bytes() + b"unexpected,row\n")
    Result = RunCatalog("VerifyCatalog.py", str(OutputPath))
    assert Result.returncode != 0
    assert "Artifact fingerprint differs: ApiTypes.csv" in Result.stderr

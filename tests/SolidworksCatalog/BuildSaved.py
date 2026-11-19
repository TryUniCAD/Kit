# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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

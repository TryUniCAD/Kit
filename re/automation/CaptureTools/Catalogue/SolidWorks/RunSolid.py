# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps
from pathlib import Path
from sys import platform

from CaptureTools.Catalogue.SolidWorks.RunSolidPhase import RunSolidPhase
from CaptureTools.Catalogue.SolidWorks.ValidateSolid import ValidateSolid
from CaptureTools.Catalogue.SolidWorks.VerifySolid import VerifySolid
from CaptureTools.Catalogue.SolidWorks.SolidHost import ValidateSolidHost


# explicit native configuration prevents catalogue data from choosing arbitrary executables
def RunSolid(CaseValue, OutputDirectory, HostConfig):
    CaseValue = ValidateSolid(CaseValue)
    if platform != "win32":
        raise ValueError("SOLIDWORKS authoring requires an isolated Windows host")
    ValidateSolidHost(HostConfig, Prepared=True)
    OutputPath = Path(OutputDirectory).resolve()
    SourceRoot = Path(__file__).resolve().parents[5]
    if OutputPath.is_relative_to(SourceRoot) or OutputPath.exists():
        raise ValueError(
            "SOLIDWORKS authoring requires a fresh directory outside the checkout"
        )
    OutputPath.mkdir(parents=True)
    CasePath = OutputPath / "ConfiguredCase.json"
    with CasePath.open("x", encoding="utf-8", newline="\n") as CaseFile:
        CaseFile.write(dumps(CaseValue, sort_keys=True, allow_nan=False) + "\n")
    for PhaseName in ("first", "second"):
        RunSolidPhase(CasePath, OutputPath, HostConfig, PhaseName)
    return VerifySolid(CaseValue, OutputPath)

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
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


# explicit native configuration prevents catalogue data from choosing arbitrary executables
def RunSolid(CaseValue, OutputDirectory, HostConfig):
    CaseValue = ValidateSolid(CaseValue)
    if platform != "win32":
        raise ValueError("SOLIDWORKS authoring requires an isolated Windows host")
    if (
        not isinstance(HostConfig, dict)
        or not {"interop_assembly", "executable"} <= HostConfig.keys()
        or HostConfig.keys() - {"interop_assembly", "executable", "phase_seconds"}
    ):
        raise ValueError("SOLIDWORKS host requires executable and interop paths")
    for PathName in ("interop_assembly", "executable"):
        PathValue = Path(HostConfig[PathName])
        if not PathValue.is_absolute() or not PathValue.is_file():
            raise ValueError("SOLIDWORKS host paths must name existing absolute files")
    PhaseSeconds = HostConfig.get("phase_seconds", 600)
    if type(PhaseSeconds) is not int or not 1 <= PhaseSeconds <= 86400:
        raise ValueError("SOLIDWORKS phase timeout must be between 1 and 86400 seconds")
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

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path
from sys import platform

from CaptureTools.Catalogue.SolidWorks.RunSolidPhase import RunSolidPhase
from CaptureTools.Catalogue.SolidWorks.SolidBatchSize import SolidBatchScale
from CaptureTools.Catalogue.SolidWorks.PrepareBatch import PrepareBatch
from CaptureTools.Catalogue.SolidWorks.VerifySolid import VerifySolid
from InferenceGrid.Authoring.NativeEnvironment import ValidateNative


# startup sharing remains bounded while every case retains independent artifacts and acceptance
def RunSolidBatch(Cases, OutputDirectory, HostConfig, Revision=None):
    if platform != "win32":
        raise ValueError("SOLIDWORKS authoring requires an isolated Windows host")
    if (
        not isinstance(HostConfig, dict)
        or not {"interop_assembly", "executable"} <= HostConfig.keys()
        or HostConfig.keys()
        - {"interop_assembly", "executable", "phase_seconds", "native_environment", "verification_mode", "routine_queue"}
    ):
        raise ValueError("SOLIDWORKS host requires executable and interop paths")
    if "native_environment" in HostConfig:
        ValidateNative(HostConfig["native_environment"])
    for PathName in ("interop_assembly", "executable"):
        PathValue = Path(HostConfig[PathName])
        if not PathValue.is_absolute() or not PathValue.is_file():
            raise ValueError("SOLIDWORKS host paths must name existing absolute files")
    PhaseSeconds = HostConfig.get("phase_seconds", 600)
    if type(PhaseSeconds) is not int or not 1 <= PhaseSeconds <= 86400:
        raise ValueError("SOLIDWORKS phase timeout must be between 1 and 86400 seconds")
    Prepared = PrepareBatch(Cases, OutputDirectory)
    Normal, CasePaths = Prepared["cases"], Prepared["outputs"]
    if "phase_seconds" not in HostConfig:
        HostConfig = {**HostConfig, "phase_seconds": 600 * SolidBatchScale(len(Normal))}
    ManifestPath, ManifestPin = Prepared["manifest"], Prepared["manifest_sha256"]
    OutputPath = ManifestPath.parent
    Routine = HostConfig.get("verification_mode") == "document_reopen"
    if Routine:
        from InferenceGrid.Authoring.SolidRoutine import RequestRoutine

        RequestRoutine(ManifestPath, HostConfig, Revision)
    for PhaseName in (() if Routine else ("first", "second")):
        RunSolidPhase(ManifestPath, OutputPath, HostConfig, PhaseName, IsBatch=True)
        if sha256(ManifestPath.read_bytes()).hexdigest() != ManifestPin:
            raise ValueError(
                "SOLIDWORKS batch manifest changed during native execution"
            )
        for CaseOutput in CasePaths:
            for Suffix in ("-owner.json", "-native.json"):
                Evidence = (OutputPath / (PhaseName + Suffix)).read_bytes()
                with (CaseOutput / (PhaseName + Suffix)).open("xb") as ReceiptFile:
                    ReceiptFile.write(Evidence)
    Reports = []
    for CaseValue, CaseOutput in zip(Normal, CasePaths, strict=True):
        try:
            Report = VerifySolid(CaseValue, CaseOutput, Routine=Routine)
        except ValueError as Error:
            Reports.append({"case": CaseValue, "native_rejection": str(Error)})
            continue
        Report["native_batch"] = {
            "manifest_sha256": ManifestPin,
            "case_count": len(Normal),
            "directory": str(OutputPath),
        }
        Reports.append(Report)
    return Reports

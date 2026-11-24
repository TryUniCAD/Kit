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
from CaptureTools.Catalogue.SolidWorks.PrepareBatch import PrepareBatch
from CaptureTools.Catalogue.SolidWorks.VerifySolid import VerifySolid
from CaptureTools.Catalogue.SolidWorks.SolidHost import ValidateSolidHost


# startup sharing remains bounded while every case retains independent artifacts and acceptance
def RunSolidBatch(Cases, OutputDirectory, HostConfig):
    if platform != "win32":
        raise ValueError("SOLIDWORKS authoring requires an isolated Windows host")
    ValidateSolidHost(HostConfig, Prepared=True)
    Prepared = PrepareBatch(Cases, OutputDirectory)
    Normal, CasePaths = Prepared["cases"], Prepared["outputs"]
    ManifestPath, ManifestPin = Prepared["manifest"], Prepared["manifest_sha256"]
    OutputPath = ManifestPath.parent
    for PhaseName in ("first", "second"):
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
        Report = VerifySolid(CaseValue, CaseOutput)
        Report["native_batch"] = {
            "manifest_sha256": ManifestPin,
            "case_count": len(Normal),
            "directory": str(OutputPath),
        }
        Reports.append(Report)
    return Reports

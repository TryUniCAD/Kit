# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import dumps
from pathlib import Path
from sys import platform

from CaptureTools.Catalogue.SolidWorks.RunSolidPhase import RunSolidPhase
from CaptureTools.Catalogue.SolidWorks.ValidateSolid import ValidateSolid
from CaptureTools.Catalogue.SolidWorks.VerifySolid import VerifySolid
from InferenceGrid.Authoring.NativeEnvironment import ValidateNative


# startup sharing remains bounded while every case retains independent artifacts and acceptance
def RunSolidBatch(Cases, OutputDirectory, HostConfig):
    if not isinstance(Cases, list) or not 1 <= len(Cases) <= 3:
        raise ValueError("SOLIDWORKS native batch requires one to three written cases")
    Normal = [ValidateSolid(CaseValue) for CaseValue in Cases]
    if any("program" not in CaseValue["options"] for CaseValue in Normal):
        raise ValueError(
            "SOLIDWORKS batching requires source pinned written recipe programs"
        )
    if platform != "win32":
        raise ValueError("SOLIDWORKS authoring requires an isolated Windows host")
    if (
        not isinstance(HostConfig, dict)
        or not {"interop_assembly", "executable"} <= HostConfig.keys()
        or HostConfig.keys()
        - {"interop_assembly", "executable", "phase_seconds", "native_environment"}
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
    OutputPath = Path(OutputDirectory).resolve()
    SourceRoot = Path(__file__).resolve().parents[5]
    if OutputPath.is_relative_to(SourceRoot) or OutputPath.exists():
        raise ValueError(
            "SOLIDWORKS native batch requires a fresh directory outside the checkout"
        )
    Configurations = [
        dumps(CaseValue, sort_keys=True, allow_nan=False) + "\n" for CaseValue in Normal
    ]
    Pins = [sha256(Content.encode()).hexdigest() for Content in Configurations]
    if len(Pins) != len(set(Pins)):
        raise ValueError("SOLIDWORKS native batch cannot repeat a configured case")
    OutputPath.mkdir(parents=True)
    Manifest = {"schema": 1, "cases": []}
    CasePaths = []
    for Content, CasePin in zip(Configurations, Pins, strict=True):
        CaseOutput = OutputPath / ("Case" + CasePin)
        CaseOutput.mkdir()
        CasePath = CaseOutput / "ConfiguredCase.json"
        with CasePath.open("x", encoding="utf-8", newline="\n") as ConfigFile:
            ConfigFile.write(Content)
        Manifest["cases"].append(
            {"configuration": str(CasePath), "output": str(CaseOutput)}
        )
        CasePaths.append(CaseOutput)
    ManifestPath = OutputPath / "BatchManifest.json"
    with ManifestPath.open("x", encoding="utf-8", newline="\n") as ManifestFile:
        ManifestFile.write(dumps(Manifest, sort_keys=True, allow_nan=False) + "\n")
    ManifestPin = sha256(ManifestPath.read_bytes()).hexdigest()
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

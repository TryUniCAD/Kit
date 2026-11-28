# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import dumps
from pathlib import Path

from CaptureTools.Catalogue.SolidWorks.SolidBatchSize import KSolidBatchCases
from CaptureTools.Catalogue.SolidWorks.ValidateSolid import ValidateSolid


# native filenames must fit application limits before a licensed process is started
def CheckBatchPaths(CaseValue, CaseOutput):
    Recipe = CaseValue["recipe"]
    Suffixes = ["baseline-a", "baseline-b"]
    if "program" in CaseValue["options"]:
        Program = CaseValue["options"]["program"]
        Suffixes.extend(
            "edit-" + Edit["parameter"] + "-" + format(Edit["value"], ".17g")
            for Edit in Program["edits"]
        )
        Suffixes.extend(Variant["name"] for Variant in Program["variants"])
    else:
        Suffixes.extend(
            "edit-" + Parameter + "-" + "0" * 32
            for Parameter in CaseValue["parameters"]
        )
        Suffixes.extend(
            ("units-inch", "plane-yz", "direction-negative", "termination-through-all")
        )
    for Suffix in Suffixes:
        NativePath = (
            CaseOutput / Recipe / (Recipe + "-solidworks-" + Suffix + ".SLDPRT")
        )
        if len(str(NativePath).encode("utf-16-le")) // 2 >= 260:
            raise ValueError(
                "SOLIDWORKS native archive path exceeds the application limit"
            )


# real disk preparation can be verified without launching the native application boundary
def PrepareBatch(Cases, OutputDirectory):
    if not isinstance(Cases, list) or not 1 <= len(Cases) <= KSolidBatchCases:
        raise ValueError(
            f"SOLIDWORKS native batch requires one to {KSolidBatchCases} configured cases"
        )
    Normal = [ValidateSolid(CaseValue) for CaseValue in Cases]
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
    CasePaths = [OutputPath / ("Case" + CasePin[:16]) for CasePin in Pins]
    if len(CasePaths) != len(set(CasePaths)):
        raise ValueError("SOLIDWORKS native batch case directory prefixes collide")
    for CaseValue, CaseOutput in zip(Normal, CasePaths, strict=True):
        CheckBatchPaths(CaseValue, CaseOutput)
    OutputPath.mkdir(parents=True)
    Manifest = {"schema": 1, "cases": []}
    for Content, CaseOutput in zip(Configurations, CasePaths, strict=True):
        CaseOutput.mkdir()
        CasePath = CaseOutput / "ConfiguredCase.json"
        with CasePath.open("x", encoding="utf-8", newline="\n") as ConfigFile:
            ConfigFile.write(Content)
        Manifest["cases"].append(
            {"configuration": str(CasePath), "output": str(CaseOutput)}
        )
    ManifestPath = OutputPath / "BatchManifest.json"
    with ManifestPath.open("x", encoding="utf-8", newline="\n") as ManifestFile:
        ManifestFile.write(dumps(Manifest, sort_keys=True, allow_nan=False) + "\n")
    return {
        "cases": Normal,
        "outputs": CasePaths,
        "manifest": ManifestPath,
        "manifest_sha256": sha256(ManifestPath.read_bytes()).hexdigest(),
        "configuration_sha256": Pins,
    }

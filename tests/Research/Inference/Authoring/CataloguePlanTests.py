# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

# process fixtures need the actual catalogue command rather than imported planning internals
KSourceRoot = FilePath(__file__).resolve().parents[4]


# representative taxonomy aliases expose executable and unsupported authoring routes together
def WriteCatalog(TmpPath: FilePath) -> FilePath:
    Families = {
        "family:sketchlines": ["corner-rectangle"],
        "family:sketchdimensions": ["linear-dimension", "diameter-dimension"],
        "family:sketchconics": ["circle"],
        "family:extrude": ["boss-base-extrude", "cut-extrude"],
        "family:fillet": ["constant-radius-fillet"],
    }
    Catalogue: dict[str, object] = {
        "schema_version": 1,
        "waves": [{"id": "alpha"}],
        "families": [
            {
                "id": Family,
                "wave": "alpha",
                "parent_id": None,
                "dependencies": [],
                "subfeatures": [
                    {"id": Family + ":" + Feature, "dependencies": [], "options": []}
                    for Feature in Features
                ],
            }
            for Family, Features in Families.items()
        ],
    }
    CatalogPath = TmpPath / "FeaturePlan.json"
    _ = CatalogPath.write_text(EncodeJson(Catalogue), encoding="utf-8")
    return CatalogPath


# actual subprocess invocation verifies argument handling destination preservation and emitted plans
def RunCatalog(TmpPath: FilePath, *Arguments: str | FilePath) -> tuple[int, str]:
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            str(KSourceRoot / "re/automation/InferenceGrid/RunFeatureCatalogue.py"),
            "--solidworks-catalogue",
            str(WriteCatalog(TmpPath)),
            "--directory",
            str(TmpPath / "Run"),
            *map(str, Arguments),
        ],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    return Result.returncode, Result.stdout + Result.stderr


# discovery authoring must deduplicate aliases without consuming reserved recipe families
def CheckDiscovery(TmpPath: FilePath) -> None:
    ExitCode, Output = RunCatalog(TmpPath, "--author-samples", "--prepare-only")
    assert ExitCode == 0, Output
    PlanValue = DecodeJson((TmpPath / "Run/AuthoringPlan.json").read_bytes())
    assert len(PlanValue["samples"]) == 3
    assert {
        Selection["case"]["recipe"] for Selection in PlanValue["samples"].values()
    } == {
        "P01",
        "P03",
        "P04",
    }
    Features = PlanValue["features"]["solidworks"]
    assert (
        Features["family:sketchlines:corner-rectangle"]["samples"]
        == Features["family:sketchdimensions:linear-dimension"]["samples"]
    )
    assert (
        Features["family:sketchconics:circle"]["status"]
        == "authoring_recipe_unavailable"
    )
    assert (
        Features["family:fillet:constant-radius-fillet"]["status"]
        == "authoring_recipe_unavailable"
    )
    assert not (TmpPath / "Run/Store").exists()


# parameter grids must retain distinct cases and reject values before touching native applications
def CheckOverrides(TmpPath: FilePath) -> None:
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "application": "solidworks",
                        "feature": "family:extrude:boss-base-extrude",
                        "parameters": {"width_mm": Width},
                        "options": {"direction": -1},
                    }
                    for Width in (43, 47)
                ],
            }
        ),
        encoding="utf-8",
    )
    ExitCode, Output = RunCatalog(
        TmpPath, "--author-samples", "--prepare-only", "--authoring-cases", CasePath
    )
    assert ExitCode == 0, Output
    PlanValue = DecodeJson((TmpPath / "Run/AuthoringPlan.json").read_bytes())
    assert len(PlanValue["samples"]) == 2
    assert {
        Selection["case"]["parameters"]["width_mm"]
        for Selection in PlanValue["samples"].values()
    } == {43, 47}
    assert all(
        Selection["case"]["options"]["direction"] == -1
        for Selection in PlanValue["samples"].values()
    )
    assert not (TmpPath / "Run/Store").exists()


# explicit evidence modes keep reserved authoring separate from ordinary discovery execution
def CheckReserved(TmpPath: FilePath) -> None:
    ExitCode, Output = RunCatalog(
        TmpPath, "--author-samples", "--prepare-only", "--capture-mode", "qualification"
    )
    assert ExitCode == 0, Output
    PlanValue = DecodeJson((TmpPath / "Run/AuthoringPlan.json").read_bytes())
    assert len(PlanValue["samples"]) == 1
    assert next(iter(PlanValue["samples"].values()))["case"]["recipe"] == "P02"


# text recipes must not be interpreted as executable native authoring instructions
def CheckRefusal(TmpPath: FilePath) -> None:
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "application": "solidworks",
                        "feature": "family:fillet:constant-radius-fillet",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    ExitCode, Output = RunCatalog(
        TmpPath, "--author-samples", "--prepare-only", "--authoring-cases", CasePath
    )
    assert ExitCode == 1 and "no executable authoring recipe" in Output
    assert not (TmpPath / "Run").exists()

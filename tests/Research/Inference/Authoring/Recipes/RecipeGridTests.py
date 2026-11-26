# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as CaseMark

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.RunCatalogue import RunCatalogue


# parameter grids must change one quantity at a time and retain three legal distinct values per quantity
@CaseMark.parametrize("Offset", (0, 5))
def CheckPlanGrid(TmpPath: FilePath, Offset: int) -> None:
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "application": "solidworks",
                        "feature": "family:extrude:offset-start-extrude",
                        "parameters": {"offset_mm": Offset},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    Process = RunCatalogue(
        TmpPath, "--authoring-cases", CasePath, "--authoring-grid", "three-values"
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    PlanValue = DecodeJson((TmpPath / "Run/AuthoringPlan.json").read_bytes())
    assert PlanValue["parameter_grid"] == "three-values"
    Params = [Entry["case"]["parameters"] for Entry in PlanValue["samples"].values()]
    Baseline = {"width_mm": 40, "height_mm": 20, "depth_mm": 10, "offset_mm": Offset}
    assert len(Params) == 1 + 2 * len(Baseline)
    assert Baseline in Params
    for Current in Params:
        assert sum(Current[Field] != Value for Field, Value in Baseline.items()) <= 1
    for Field in Baseline:
        assert len({Current[Field] for Current in Params}) == 3
    assert not (TmpPath / "Run/Store").exists()


# resuming a saved run cannot silently replace its source pinned parameter grid
def CheckResumeGrid(TmpPath: FilePath) -> None:
    Prepared = RunCatalogue(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    Before = (TmpPath / "Run/AuthoringPlan.json").read_bytes()
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/InferenceGrid/RunFeatureCatalogue.py"),
            "--directory",
            str(TmpPath / "Run"),
            "--resume",
            "--authoring-grid",
            "three-values",
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == 1
    assert "without new input or worker options" in Process.stderr
    assert (TmpPath / "Run/AuthoringPlan.json").read_bytes() == Before
    assert not (TmpPath / "Run/Store").exists()


# coupled radii near a domain boundary still need three physically distinct legal grid values
def CheckTightGrid(TmpPath: FilePath) -> None:
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "application": "solidworks",
                        "feature": "family:revolve:cut-revolve",
                        "parameters": {"inner_radius_mm": 9.9, "outer_radius_mm": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    Process = RunCatalogue(
        TmpPath,
        "--capture-mode",
        "holdout",
        "--authoring-cases",
        CasePath,
        "--authoring-grid",
        "three-values",
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    PlanValue = DecodeJson((TmpPath / "Run/AuthoringPlan.json").read_bytes())
    Params = [Entry["case"]["parameters"] for Entry in PlanValue["samples"].values()]
    assert len(Params) == 9
    assert len({Entry["outer_radius_mm"] for Entry in Params}) == 3
    assert all(
        Entry["inner_radius_mm"] < Entry["outer_radius_mm"] <= 10 for Entry in Params
    )
    assert not (TmpPath / "Run/Store").exists()

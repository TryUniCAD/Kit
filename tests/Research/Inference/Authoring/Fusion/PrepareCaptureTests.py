# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from subprocess import run as RunCommand
from sys import executable as PythonExe

from tests.Research.Inference.Authoring.Fusion.CaptureFixture import (
    CaptureFixture,
    KCaptureTool,
)
from tests.Research.Inference.Authoring.Fusion.RunPreparation import RunPreparation


# custom dimensions must survive the public planner and exact native artifact roster derivation
def CheckPlan(TmpPath: FilePath) -> None:
    SourceRoot = CaptureFixture(TmpPath)
    Cases = [
        {
            "recipe": "P03",
            "parameters": {"width_mm": 51, "height_mm": 31, "depth_mm": 17},
            "options": {"basis": "YZ", "direction": -1},
        },
        {
            "recipe": "P04",
            "parameters": {
                "width_mm": 63,
                "height_mm": 32,
                "depth_mm": 19,
                "cut_width_mm": 13,
                "cut_height_mm": 9,
            },
            "options": {"termination": "through_all"},
        },
    ]
    ExitCode, Output, Errors, Prepared = RunPreparation(SourceRoot, TmpPath, Cases)
    assert ExitCode == 0, Errors
    Reply = ReadJson(Output)
    RawBytes = (Prepared / "plan.json").read_bytes()
    PlanData = ReadJson(RawBytes)
    assert HashBytes(RawBytes).hexdigest() == Reply["plan_sha256"]
    assert PlanData["scope"] == "catalogue-parametric-fusion"
    assert PlanData["cases"][0]["parameters"]["depth_mm"] == 17
    assert PlanData["cases"][0]["options"]["direction"] == -1
    assert "cut_depth_mm" not in PlanData["cases"][1]["parameters"]
    Program = "from json import loads as ReadJson,dumps as WriteJson; from runpy import run_path as LoadScript; from sys import argv as ArgValues; from pathlib import Path as FilePath; Module=LoadScript(ArgValues[1]); PlanData=ReadJson(FilePath(ArgValues[2]).read_bytes()); Module['ValidatePlan'](PlanData); from CaptureTools.Catalogue.Fusion.FusionExpected import ExpectFusion; from CaptureTools.Catalogue.Fusion.FusionBatch import ModelCase; print(WriteJson({'paths':{Phase:Module['PhasePaths'](PlanData,Phase) for Phase in ('a','b')},'expected':[ExpectFusion(ModelCase(Case)) for Case in PlanData['cases']]}))"
    Checked = RunCommand(
        [
            PythonExe,
            "-B",
            "-c",
            Program,
            str(SourceRoot / KCaptureTool),
            str(Prepared / "plan.json"),
        ],
        cwd=SourceRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Checked.returncode == 0, Checked.stderr
    Result = ReadJson(Checked.stdout)
    Paths = Result["paths"]
    assert len(Paths["a"]) == 4 and len(Paths["b"]) == 12
    assert all(FilePath(Value).parts[0] == "phase-b" for Value in Paths["b"].values())
    assert Result["expected"][0]["volume_mm3"] == 26877
    assert Result["expected"][0]["center_of_mass_mm"] == [-8.5, 25.5, 15.5]
    assert Result["expected"][1]["volume_mm3"] == 36081
    assert Result["expected"][1]["center_of_mass_mm"] == [31.5, 16, 9.5]
    assert not any(Prepared.glob("*.f3d"))


# source identity and native evidence reservations must fail closed through actual preparation processes
def CheckRefusals(TmpPath: FilePath) -> None:
    SourceRoot = CaptureFixture(TmpPath)
    Rejections = [
        ([{"recipe": "P02"}], "reserved for another evidence mode"),
        ([{"recipe": "P04", "parameters": {"cut_width_mm": 50}}], "strictly inside"),
        (
            [
                {
                    "recipe": "P04",
                    "parameters": {"cut_depth_mm": 4},
                    "options": {"termination": "through_all"},
                }
            ],
            "no driving cut depth",
        ),
        ([{"recipe": "P03", "parameters": {"depth_mm": True}}], "finite between"),
        ([{"recipe": "P01"}, {"recipe": "P01"}], "changed or duplicated"),
        ([{"recipe": "P01"}] * 3, "one or two"),
    ]
    for Index, (Cases, Diagnostic) in enumerate(Rejections):
        ExitCode, _, Errors, Prepared = RunPreparation(
            SourceRoot, TmpPath, Cases, RunName=f"Refusal{Index}"
        )
        assert ExitCode == 1 and Diagnostic in Errors
        assert not Prepared.exists()
    Changed = SourceRoot / "re/automation/CaptureTools/Catalogue/Fusion/BuildFusion.py"
    _ = Changed.write_bytes(Changed.read_bytes() + b"\n")
    ExitCode, _, Errors, Prepared = RunPreparation(
        SourceRoot, TmpPath, [{"recipe": "P01"}], RunName="Tampered"
    )
    assert ExitCode == 1 and "differs from the reviewed revision" in Errors
    assert not Prepared.exists()


# explicit qualification and holdout modes must preserve their separate native evidence lineages
def CheckModes(TmpPath: FilePath) -> None:
    SourceRoot = CaptureFixture(TmpPath)
    for ModeName, Recipe in (("qualification", "P02"), ("holdout", "P05")):
        ExitCode, Output, Errors, Prepared = RunPreparation(
            SourceRoot, TmpPath, [{"recipe": Recipe}], ModeName, ModeName
        )
        assert ExitCode == 0, Errors
        Reply = ReadJson(Output)
        assert Reply["mode"] == ModeName and Reply["cases"][0]["recipe"] == Recipe
        assert (Prepared / "plan.json").is_file()
        ExitCode, _, Errors, Prepared = RunPreparation(
            SourceRoot, TmpPath, [{"recipe": "P03"}], ModeName, ModeName + "Mismatch"
        )
        assert ExitCode == 1 and "reserved for another evidence mode" in Errors
        assert not Prepared.exists()

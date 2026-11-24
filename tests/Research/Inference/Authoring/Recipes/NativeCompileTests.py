# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.SolidWorks.CompileCapture import CompileCapture
from tests.Research.Inference.Authoring.Recipes.CompileCases import KCompileCases
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe
from tests.Research.Inference.Authoring.Recipes.Windows.RunBatchProbe import (
    RunBatchProbe,
)


# registered native interop must compile and validate every typed program before any application startup
@CaseMark.parametrize("RecipeKey,Params", KCompileCases)
def CheckInterop(TmpPath: FilePath, RecipeKey: str, Params: dict[str, float]) -> None:
    Compiled = RunProbe(TmpPath, "compile", {"recipe": RecipeKey, "parameters": Params})
    assert Compiled.returncode == 0, Compiled.stderr
    CasePath = TmpPath / "Case.json"
    _ = CasePath.write_text(Compiled.stdout, encoding="utf-8")
    OutputPath = TmpPath / "Capture"
    Process = CompileCapture(CasePath, OutputPath)
    assert Process.returncode == 0, Process.stdout + Process.stderr
    assert "without starting an application" in Process.stdout
    assert not OutputPath.exists()


# the native batch consumer must validate paired and written cases together before launching any application
@CaseMark.parametrize(
    "Recipes",
    (("P01", "P03", "P04"), ("P02", "extrude-midplane", "P05")),
)
def CheckBatchTypes(TmpPath: FilePath, Recipes: tuple[str, ...]) -> None:
    OutputPath = TmpPath / "Capture"
    Prepared = RunBatchProbe(
        TmpPath, OutputPath, [{"recipe": Recipe} for Recipe in Recipes]
    )
    assert Prepared.returncode == 0, Prepared.stderr
    Manifest = FilePath(DecodeJson(Prepared.stdout)["manifest"])
    Process = CompileCapture(Manifest, OutputPath, BatchMode=True)
    assert Process.returncode == 0, Process.stdout + Process.stderr
    assert "without starting an application" in Process.stdout
    assert not (OutputPath / "first-owner.json").exists()


# an altered typed program cannot bypass recomputation at the compiled native consumer boundary
def CheckInteropPin(TmpPath: FilePath) -> None:
    Compiled = RunProbe(TmpPath, "compile", {"recipe": "extrude-midplane"})
    assert Compiled.returncode == 0, Compiled.stderr
    CaseValue = DecodeJson(Compiled.stdout)
    CaseValue["options"]["program"]["operation"]["effect"] = "cut"
    CasePath = TmpPath / "Case.json"
    _ = CasePath.write_text(EncodeJson(CaseValue), encoding="utf-8")
    OutputPath = TmpPath / "Capture"
    Process = CompileCapture(CasePath, OutputPath)
    assert Process.returncode != 0
    assert not OutputPath.exists()

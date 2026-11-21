# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.CompileCases import (
    KCompileCases,
    KInvalidCases,
)
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe


# real process compilation must produce canonical complete programs and accept only its own unchanged recomputation
@CaseMark.parametrize("RecipeKey,Params", KCompileCases)
def CheckCompile(TmpPath: FilePath, RecipeKey: str, Params: dict[str, float]) -> None:
    Process = RunProbe(TmpPath, "compile", {"recipe": RecipeKey, "parameters": Params})
    assert Process.returncode == 0, Process.stderr
    Compiled = DecodeJson(Process.stdout)
    assert set(Compiled) == {"recipe", "parameters", "options"}
    assert Compiled["recipe"] == RecipeKey
    assert all(
        Compiled["parameters"][ParamName] == Value
        for ParamName, Value in Params.items()
    )
    Program = Compiled["options"]["program"]
    assert Program["schema"] == 1 and type(Program["schema"]) is int
    assert Program["operation"]["kind"] == RecipeKey.split("-", 1)[0]
    assert set(Program["bindings"]) == set(Compiled["parameters"])
    assert Program["edits"]
    Repeated = RunProbe(TmpPath, "compile", Compiled)
    assert Repeated.returncode == 0, Repeated.stderr
    assert DecodeJson(Repeated.stdout) == Compiled


# unsupported controls are rejected by a fresh interpreter before native authoring can be scheduled
@CaseMark.parametrize("CaseValue", KInvalidCases)
def CheckBadInputs(TmpPath: FilePath, CaseValue: dict[str, object]) -> None:
    Process = RunProbe(TmpPath, "compile", CaseValue)
    assert Process.returncode != 0
    assert "ValueError" in Process.stderr
    assert not Process.stdout.strip()


# the reserved program field cannot alter operation identity source binding or parameter ownership
@CaseMark.parametrize("Fault", ("schema", "effect", "owner", "source"))
def CheckProgramPin(TmpPath: FilePath, Fault: str) -> None:
    Process = RunProbe(TmpPath, "compile", {"recipe": "extrude-midplane"})
    assert Process.returncode == 0, Process.stderr
    Compiled = DecodeJson(Process.stdout)
    Program = Compiled["options"]["program"]
    if Fault == "schema":
        Program["schema"] = True
    elif Fault == "effect":
        Program["operation"]["effect"] = "cut"
    elif Fault == "owner":
        Program["bindings"]["depth_mm"]["owner"] = "UnrelatedFeature"
    else:
        Program["recipe_sha256"] = "0" * 64
    Repeated = RunProbe(TmpPath, "compile", Compiled)
    assert Repeated.returncode != 0
    assert "exact recipe recomputation" in Repeated.stderr

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from pytest import mark as CaseMark
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# prerequisites must block at the command boundary before provider or native dispatch
@CaseMark.parametrize(
    "HasAuth,HasMetadata,ExtraArgs,Expected",
    [
        (False, True, (), "generation_not_authorized"),
        (True, False, (), "api_metadata_missing"),
        (
            True,
            True,
            ("--builder-feature", "family:planes:three-points"),
            "verifier_support_missing",
        ),
    ],
)
def CheckBlockers(
    TmpPath: FilePath,
    HasAuth: bool,
    HasMetadata: bool,
    ExtraArgs: tuple[str, ...],
    Expected: str,
) -> None:
    WriteInputs(TmpPath)
    Process = RunBuilder(TmpPath, *ExtraArgs, HasAuth=HasAuth, HasMetadata=HasMetadata)
    assert Process.returncode == 3, Process.stdout + Process.stderr
    Result = DecodeJson(Process.stdout)
    assert Result["classification"].startswith(Expected)
    assert Result["builder_qualified"] is False
    assert Result["conversion_qualified"] is False
    assert not (TmpPath / "Run/Store").exists()
    assert not (TmpPath / "Run/Generation").exists()


# invalid budgets must fail before creating a durable run or spending authorization
@CaseMark.parametrize(
    "OptionName", ["--builder-model-calls", "--builder-attempts", "--builder-seconds"]
)
def CheckBudget(TmpPath: FilePath, OptionName: str) -> None:
    WriteInputs(TmpPath)
    Process = RunBuilder(TmpPath, OptionName, "0")
    assert Process.returncode == 2
    assert not (TmpPath / "Run").exists()

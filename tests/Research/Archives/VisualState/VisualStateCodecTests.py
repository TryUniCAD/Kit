# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson

from pytest import mark as MarkCases

from tests.Research.Archives.VisualState.VisualStateProcess import (
    KCodecProgram,
    RunVisualCase,
)


# authored identities and names prevent a saved default stream from satisfying the inverse check
@MarkCases.parametrize(
    "FeatureCount, MixedFlags", [(0, False), (1, False), (5, True), (20, True)]
)
def CheckAuthored(FeatureCount: int, MixedFlags: bool) -> None:
    Settings = {
        "appearance": 0x123456789AB,
        "visible": False,
        "mixed": MixedFlags,
        "features": FeatureCount,
        "representation": 471,
        "name": "caller state Ω " * 40,
    }
    Result = RunVisualCase(KCodecProgram, Settings)
    assert Result.returncode == 0, Result.stderr
    Report = ParseJson(Result.stdout)
    assert Report["owners"] == FeatureCount + 1
    assert Report["appearance"] == Settings["appearance"]
    assert Report["representation"] == Settings["representation"]
    assert Report["name"] == Settings["name"]


# unsafe references and unsupported field branches must fail across the executable archive boundary
@MarkCases.parametrize(
    "InvalidCase",
    [
        "duplicate",
        "holder",
        "visibility",
        "display",
        "locator",
        "clock",
        "zero",
        "truncated",
        "trailing",
    ],
)
def CheckMalformed(InvalidCase: str) -> None:
    Settings = {
        "appearance": 127,
        "visible": True,
        "mixed": True,
        "features": 5,
        "representation": 31,
        "name": "independent malformed case",
        "invalid": InvalidCase,
    }
    Result = RunVisualCase(KCodecProgram, Settings)
    assert Result.returncode == 0, Result.stderr
    assert ParseJson(Result.stdout) == {"rejected": InvalidCase}


# equal display attributes should share references while distinct explicit settings allocate their own objects
def CheckSharing() -> None:
    Settings = {
        "appearance": 2081,
        "visible": False,
        "mixed": False,
        "features": 5,
        "representation": 89,
        "name": "owned sharing state",
    }
    Shared = RunVisualCase(KCodecProgram, Settings)
    Distinct = RunVisualCase(KCodecProgram, {**Settings, "mixed": True})
    assert Shared.returncode == Distinct.returncode == 0, (
        Shared.stderr,
        Distinct.stderr,
    )
    SharedReport, DistinctReport = ParseJson(Shared.stdout), ParseJson(Distinct.stdout)
    assert SharedReport["bytes"] + 20 == DistinctReport["bytes"]
    assert SharedReport["sha256"] != DistinctReport["sha256"]

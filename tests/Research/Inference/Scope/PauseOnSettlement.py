# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as Environment
from pathlib import Path as FilePath
from sys import argv as Arguments, getprofile as GetProfile, setprofile as SetProfile
from types import FrameType

from tests.Research.Inference.Scope.IsSettlement import IsSettlement
from tests.Research.Inference.Scope.WaitForPause import WaitForPause


# the startup hook selects the intended executable and its actual pause marker path
def InstallPause() -> None:
    Owner = Environment.get("KIT_TEST_PAUSE_OWNER")
    if not Owner or Arguments[0] != Owner or "--catalogue-pause-file" not in Arguments:
        return
    MarkArg = Arguments.index("--catalogue-pause-file") + 1
    Pause = Environment["KIT_TEST_PAUSE_MARKER"]
    if Arguments[MarkArg] != Pause:
        return
    ReadyPath = FilePath(Environment["KIT_TEST_PAUSE_READY"])
    PausePath = FilePath(Pause)
    Previous = GetProfile()

    # restoring the prior profiler confines the boundary to the first accepted settlement
    def BeforeFill(Frame: FrameType, Event: str, Argument: object) -> None:
        if IsSettlement(Frame, Event, Owner):
            SetProfile(Previous)
            WaitForPause(ReadyPath, PausePath)

    SetProfile(BeforeFill)


InstallPause()

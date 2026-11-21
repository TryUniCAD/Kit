# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as Environment
from pathlib import Path as FilePath
from sys import argv as Arguments, getprofile as GetProfile, setprofile as SetProfile
from time import monotonic as Clock, sleep as WaitFor
from types import FrameType


# a completed report happens after receipt publication and before the next admission
def IsSettlement(Frame: FrameType, Event: str, Owner: str) -> bool:
    if (
        Event != "return"
        or Frame.f_code.co_filename != Owner
        or Frame.f_code.co_qualname != "Supervisor.report"
        or Frame.f_locals.get("action") != "finished"
    ):
        return False
    Detail = Frame.f_locals["detail"]
    return bool(Detail.get("outcome") == "completed" and Detail.get("stale") is False)


# only the genuine pause command can release the test supervisor to check its marker
def WaitForPause(ReadyPath: FilePath, PausePath: FilePath) -> None:
    ReadyPath.touch(exist_ok=False)
    Deadline = Clock() + 10
    while not PausePath.is_file():
        if Clock() >= Deadline:
            raise TimeoutError("catalogue pause command did not publish its marker")
        WaitFor(0.01)


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

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import Popen as OpenProcess
from time import monotonic as ElapsedTime, sleep as WaitMoment


# an early listener failure must surface before a client consumes its deadline
def WaitReadback(TmpPath: FilePath, Listener: "OpenProcess[str]") -> None:
    Deadline = ElapsedTime() + 20
    while not (TmpPath / "Endpoint/ready.json").exists():
        assert Listener.poll() is None, Listener.communicate(timeout=5)
        assert ElapsedTime() < Deadline, "readback fixture listener did not start"
        WaitMoment(0.02)

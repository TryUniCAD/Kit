# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from _thread import interrupt_main as InterruptMain
from pathlib import Path as FilePath
from signal import Signals
from time import monotonic as ReadClock, sleep as WaitSeconds


# cancellation must reach the launcher only after its real supervised process tree exists
def InterruptReady(RecordPath: FilePath, SignalName: str) -> None:
    UntilTime = ReadClock() + 45
    while ReadClock() < UntilTime:
        if RecordPath.is_file():
            _ = RecordPath.with_name("Interrupted").write_text(SignalName)
            InterruptMain(Signals[SignalName])
            return
        WaitSeconds(0.01)
    raise RuntimeError("Windows supervised worker did not report readiness")

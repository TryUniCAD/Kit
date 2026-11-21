# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from time import monotonic as Clock, sleep as WaitFor


# only the genuine pause command can release the test supervisor to check its marker
def WaitForPause(ReadyPath: FilePath, PausePath: FilePath) -> None:
    ReadyPath.touch(exist_ok=False)
    Deadline = Clock() + 10
    while not PausePath.is_file():
        if Clock() >= Deadline:
            raise TimeoutError("catalogue pause command did not publish its marker")
        WaitFor(0.01)

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import DEVNULL as NullStream, Popen as StartProcess
from sys import executable as PythonExe


# retained child identities prove provider cleanup includes descendants rather than only its direct process
def StartChild(LogPath: FilePath) -> None:
    ChildProc = StartProcess(
        [PythonExe, "-B", "-c", "import time; time.sleep(60)"],
        stdout=NullStream,
        stderr=NullStream,
    )
    with LogPath.open("a", encoding="utf-8") as LogFile:
        _ = LogFile.write(EncodeJson({"descendant": ChildProc.pid}) + "\n")

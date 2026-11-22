# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import Popen as StartProcess
from sys import argv as ArgValues, executable as PythonExe
from time import sleep as SleepTime


# real descendant lifetimes expose cleanup behavior across the provider process boundary
def MainChild() -> int:
    ModeName = ArgValues[1]
    if ModeName == "exit":
        print(EncodeJson({"completed": True}), flush=True)
        return 0
    if ModeName in {"descendant", "parentexit"}:
        ChildProc = StartProcess([PythonExe, "-B", str(FilePath(__file__)), "wait"])
        print(EncodeJson({"child_pid": ChildProc.pid}), flush=True)
        if ModeName == "parentexit":
            return 0
    if ModeName == "overflow":
        print("x" * 1024, flush=True)
    SleepTime(60)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainChild())

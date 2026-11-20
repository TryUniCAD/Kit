# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps, loads
from os import environ
from pathlib import Path
from sys import argv, executable, path

# the boundary must use this checkout rather than an installed research package
KSourceRoot = Path(__file__).resolve().parents[5]

path.insert(0, str(KSourceRoot / "re/automation"))

from CaptureTools.Catalogue.SolidWorks.NativeSolidEnv import NativeSolidEnv
from WindowsProcess import WindowsProcess


# a disposable operating system child proves the effective native environment without launching cad
def RunNativeChild() -> None:
    if argv[1] == "inner":
        print(
            dumps(
                {
                    "profile": environ.get("USERPROFILE"),
                    "roaming": environ.get("APPDATA"),
                    "temp": environ.get("TEMP"),
                    "secret": environ.get("KIT_PRIVATE_SECRET"),
                    "pythonpath": environ.get("PYTHONPATH"),
                }
            )
        )
        return
    Settings = loads(Path(argv[1]).read_bytes())
    OutputPath = Path(argv[2])
    Environment = NativeSolidEnv(Settings)
    with (
        (OutputPath / "Child.stdout").open("xb") as Output,
        (OutputPath / "Child.stderr").open("xb") as Errors,
    ):
        Process = WindowsProcess(
            [executable, "-B", str(Path(__file__).resolve()), "inner"],
            KSourceRoot,
            Environment,
            Output.fileno(),
            Errors.fileno(),
        )
        try:
            ExitCode = Process.wait(timeout=20)
            Process.finish()
            if ExitCode:
                raise RuntimeError("native environment fixture child failed")
        finally:
            Process.close()


if __name__ == "__main__":
    RunNativeChild()

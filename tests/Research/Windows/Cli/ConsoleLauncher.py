# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from sys import argv as KArguments
from threading import Thread

from KitCli.MainEntry import MainEntry
from tests.Research.Windows.Cli.InterruptReady import InterruptReady


# a private console keeps native control events isolated from the test runner and desktop
def LaunchConsole() -> int:
    RecordName, RootName, ConfigName, SignalName = KArguments[1:]
    Watcher = Thread(
        target=InterruptReady,
        args=(FilePath(RecordName), SignalName),
        daemon=True,
    )
    KArguments[:] = [
        "kit",
        "research",
        "--root",
        RootName,
        "supervisor",
        "--config",
        ConfigName,
        "run",
        "--max-seconds",
        "60",
    ]
    Watcher.start()
    return MainEntry()


if __name__ == "__main__":
    raise SystemExit(LaunchConsole())

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from subprocess import Popen, STDOUT, TimeoutExpired
from time import monotonic


# coordinator failure must stop supervised claims without terminating native user applications
def WatchSupervisor(Command, SourceRoot, LogFile, TimeoutValue, CheckRunning):
    Deadline = monotonic() + TimeoutValue
    Process = Popen(Command, cwd=SourceRoot, stdout=LogFile, stderr=STDOUT)
    try:
        while Process.poll() is None:
            CheckRunning()
            Remaining = Deadline - monotonic()
            if Remaining <= 0:
                raise TimeoutExpired(Command, TimeoutValue)
            try:
                Process.wait(timeout=min(0.25, Remaining))
            except TimeoutExpired:
                continue
        CheckRunning()
        return Process
    finally:
        if Process.poll() is None:
            Process.terminate()
            try:
                Process.wait(timeout=30)
            except TimeoutExpired:
                Process.kill()
                Process.wait(timeout=10)

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import cache as OncePerProcess
from pathlib import Path as FilePath
from subprocess import TimeoutExpired as ProcessTimeout, run as RunProcess
from time import perf_counter as ClockTime

from tests.Research.SupervisorClient import KRepoRoot

# cold runner startup needs headroom beyond the observed censored warmup while later processes load the same assembly
KColdCompileSeconds = 360


# the first managed compiler start of a runner must not consume a fixture deadline meant for warm runs
@OncePerProcess
def WarmProgress() -> None:
    Started = ClockTime()
    try:
        Result = RunProcess(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(FilePath(__file__).with_name("ProgressFixture.ps1")),
                "-Source",
                str(
                    KRepoRoot
                    / "re/automation/CaptureTools/SolidWorksAuthoring/ReadbackProgress.cs"
                ),
                "-CompileOnly",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=KColdCompileSeconds,
        )
    except ProcessTimeout as Failure:
        print(Failure.stderr)
        raise
    finally:
        print(f"readback warmup process seconds: {ClockTime() - Started:.3f}")
    assert Result.returncode == 0, Result.stdout + Result.stderr
    print(Result.stderr, end="")

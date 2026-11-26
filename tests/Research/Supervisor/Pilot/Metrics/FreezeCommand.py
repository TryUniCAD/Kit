# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Supervisor.Pilot.Metrics.PilotClient import RunReport


# process scenarios share exact freeze arguments while retaining explicit refusal expectations
def FreezeCommand(
    RootPath: FilePath,
    RunRoot: FilePath,
    BundleRoot: FilePath,
    *Options: str,
    ExitCode: int = 0,
) -> dict[str, object]:
    return RunReport(
        RootPath,
        "freeze",
        "--run",
        str(RunRoot),
        "--output",
        str(BundleRoot),
        *Options,
        ExitCode=ExitCode,
    )

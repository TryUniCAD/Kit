# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Supervisor.Pilot.Metrics.PilotClient import RunReport


# snapshot replay must always require the externally retained digest at its public boundary
def ReplayCommand(
    RootPath: FilePath, BundleRoot: FilePath, ExpectedHash: str, ExitCode: int = 0
) -> dict[str, object]:
    return RunReport(
        RootPath,
        "replay",
        "--snapshot",
        str(BundleRoot),
        "--snapshot-sha256",
        ExpectedHash,
        ExitCode=ExitCode,
    )

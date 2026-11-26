# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.Supervisor.Pilot.Metrics.EvidenceFiles import EvidenceFiles
from tests.Research.Supervisor.Pilot.Metrics.FreezeCommand import FreezeCommand


# private source manifests must bind the exact event window returned by the real activity report
def FreezeEvidence(
    RootPath: FilePath, RunRoot: FilePath, BundleRoot: FilePath
) -> dict[str, object]:
    FirstRoot = RootPath / "First"
    InputPins = FreezeCommand(RootPath, RunRoot, FirstRoot)
    Activity = JsonCodec.loads((FirstRoot / "Report.json").read_bytes())[
        "controller_activity"
    ]
    Window = {
        Field: Activity[Field]
        for Field in (
            "from_unix_seconds",
            "until_unix_seconds",
            "after_event_id",
            "through_event_id",
            "selected_events_sha256",
        )
    }
    Manifest, ManifestHash = EvidenceFiles(RootPath, Window)
    return FreezeCommand(
        RootPath,
        RunRoot,
        BundleRoot,
        "--until-unix",
        str(InputPins["until_unix_seconds"]),
        "--through",
        str(InputPins["through_event_id"]),
        "--evidence-manifest",
        str(Manifest),
        "--evidence-sha256",
        ManifestHash,
    )

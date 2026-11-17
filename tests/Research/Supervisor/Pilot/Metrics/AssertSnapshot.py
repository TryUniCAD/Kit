# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
from pathlib import Path as FilePath


# one real frozen run must distinguish completed work dependent parking and absent independent gains
def AssertSnapshot(BundleRoot: FilePath) -> None:
    Report = JsonCodec.loads((BundleRoot / "Report.json").read_bytes())
    assert Report["throughput"]["settled_completed_attempts"] == 1
    assert Report["throughput"]["completed_jobs_at_queue_observation"] == 1
    assert Report["observation"]["window_status"] == "in_progress"
    assert Report["independent_evidence"]["acceptance"]["verified_gains_claimed"] == 0
    assert Report["queue_observation"]["states"] == {
        "completed": 1,
        "waiting_evidence": 2,
    }
    Dependent = next(
        Entry
        for Entry in Report["queue_observation"]["jobs"]
        if Entry["id"] == "pilot:dependent"
    )
    assert Dependent["attempts"] == 0 and Dependent["depends_on"] == ["pilot:parked"]
    assert Report["watchdog"]["healthy_supervisor_heartbeat_samples"] == 0
    assert (
        Report["watchdog"][
            "max_seconds_between_healthy_supervisor_samples_including_boundaries"
        ]
        == Report["observation"]["observed_seconds"]
    )

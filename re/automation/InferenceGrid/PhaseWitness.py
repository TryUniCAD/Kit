# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math
import re
import time

from FusionPhasePlan import phase_process
from PairedCaptureIntake import require


# matching process numbers cannot substitute for the same recorded application lifetime
def CheckPhaseLife(dispatch, report, records, queue, phase):
    host = dispatch["host"]
    process = report["process"]
    ended = report["ended_unix_seconds"]
    finished = dispatch["finished_at"]
    require(
        type(host["pid"]) is int
        and host["pid"] > 1
        and type(process["start_unix_seconds"]) is int
        and process == phase_process(host),
        "scope grid process birth differs from its dispatch host",
    )
    clocks = (process["start_unix_seconds"], ended, finished)
    require(
        all(type(value) in (int, float) and math.isfinite(value) for value in clocks)
        and 0 < clocks[0] <= ended <= finished <= time.time(),
        "scope grid phase chronology differs from its process and dispatch",
    )
    started = report.get("started_unix_seconds")
    require(
        type(started) in (int, float)
        and math.isfinite(started)
        and clocks[0] <= started < ended,
        "scope grid phase start differs from its process and end",
    )
    handoff = dispatch["proof"].get("restart_handoff")
    require(
        records.get("restart_handoff") == handoff,
        "scope grid restart handoff differs from its accepted result",
    )
    if phase == "a":
        require(
            isinstance(handoff, dict)
            and set(handoff)
            == {
                "installation",
                "job_id",
                "reason",
                "host",
                "plan_sha256",
                "at",
                "owner",
            }
            and handoff["installation"] == queue["installation"]
            and handoff["plan_sha256"] == queue["plan_sha256"]
            and handoff["host"] == host
            and handoff["reason"] == "restart_required"
            and handoff["owner"] == "external_application_owner"
            and isinstance(handoff["job_id"], str)
            and re.fullmatch("[0-9a-f]{32}", handoff["job_id"])
            and type(handoff["at"]) in (int, float)
            and math.isfinite(handoff["at"])
            and ended <= handoff["at"] <= finished,
            "scope grid phase A lacks its exact owned restart handoff",
        )
    else:
        require(handoff is None, "scope grid phase B cannot require another restart")


# a reopened observation must describe the exact archives sealed by the authoring phase
def CheckSavedPair(first, second):
    require(
        all(
            before["archive"] == after["archive"]
            for before, after in zip(first["cases"], second["cases"], strict=True)
        ),
        "scope grid phase B archives differ from accepted phase A",
    )

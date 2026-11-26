# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path

from tests.Research.Inference.Scope.InvokeAuto import InvokeAuto


# the controller queue and parked receipt must keep their identities after repeated submission
def CheckHandoffQ(
    Store: Path,
    KindName: str,
    Route: str,
    Arguments: tuple[str | Path, ...],
    PhaseJobs: dict[str, str],
    Origin: str,
) -> None:
    Repeated = json.loads(InvokeAuto(Route, *Arguments, "submit"))
    assert len(Repeated["jobs"]) == 3
    assert not any(
        JobInfo["attempts"]
        for JobInfo in Repeated["jobs"]
        if JobInfo["kind"] == "inference.rescan"
    )
    Controller = ("--store", Store)
    Queue = json.loads(InvokeAuto("Controller.py", *Controller, "status"))["jobs"]
    assert len(Queue) == 5
    assert {JobInfo["id"] for JobInfo in Queue if JobInfo["kind"] == KindName} == set(
        PhaseJobs.values()
    )
    assert (
        json.loads(InvokeAuto("Controller.py", *Controller, "artifact", Origin))[
            "sha256"
        ]
        == Origin
    )

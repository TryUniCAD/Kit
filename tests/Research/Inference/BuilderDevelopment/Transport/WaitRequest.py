# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from time import monotonic as MonoTime, sleep as WaitBriefly

from tests.Research.Inference.BuilderDevelopment.Optimizations.JsonBoundary import (
    AsRecord,
    AsRecords,
)


# cancellation must follow the actual client acknowledgement rather than merely observing a sent request
def WaitRequest(Session: object) -> None:
    Deadline = MonoTime() + 5
    while MonoTime() < Deadline:
        for EventValue in AsRecords(getattr(Session, "events")):
            ResultValue = EventValue.get("result")
            if ResultValue is not None and AsRecord(ResultValue).get("turn") == {
                "id": "fixture-turn-1"
            }:
                return
        WaitBriefly(0.01)
    raise AssertionError(
        "provider turn was not acknowledged before cancellation deadline"
    )

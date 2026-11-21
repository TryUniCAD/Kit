# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from types import FrameType


# a completed report happens after receipt publication and before the next admission
def IsSettlement(Frame: FrameType, Event: str, Owner: str) -> bool:
    if (
        Event != "return"
        or Frame.f_code.co_filename != Owner
        or Frame.f_code.co_qualname != "Supervisor.report"
        or Frame.f_locals.get("action") != "finished"
    ):
        return False
    Detail = Frame.f_locals["detail"]
    return bool(Detail.get("outcome") == "completed" and Detail.get("stale") is False)

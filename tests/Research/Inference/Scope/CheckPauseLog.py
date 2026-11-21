# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath


# the admission assertion must include the interval before the pause acknowledgement
def CheckPauseLog(LogPath: FilePath) -> None:
    Events = [
        DecodeJson(LineText)
        for LineText in LogPath.read_text(encoding="utf-8").splitlines()
    ]
    Settlement = next(
        Index
        for Index, Event in enumerate(Events)
        if Event.get("event") == "finished"
        and Event.get("outcome") == "completed"
        and Event.get("stale") is False
    )
    PauseIndex = next(
        Index
        for Index, Event in enumerate(Events)
        if Event.get("event") == "catalogue_paused"
    )
    assert Settlement < PauseIndex
    assert all(
        Event.get("event") not in {"started", "setup_failed"}
        for Event in Events[Settlement + 1 :]
    )

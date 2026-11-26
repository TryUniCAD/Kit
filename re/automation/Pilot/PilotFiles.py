# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import os
from pathlib import Path


# exact file bytes bind configuration and evidence across unattended restarts
def FileDigest(Pathname):
    return hashlib.sha256(Path(Pathname).read_bytes()).hexdigest()


# exclusive creation prevents a preparation retry from overwriting retained evidence
def WriteRecord(Pathname, Record):
    with Path(Pathname).open("x", encoding="utf-8", newline="\n") as Output:
        json.dump(
            Record, Output, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        Output.write("\n")
        Output.flush()
        os.fsync(Output.fileno())
    return Path(Pathname)


# a durable append journal preserves observed watchdog activity after a crash
def AppendEvent(Directory, Event, **Fields):
    import time

    RunId = json.loads((Path(Directory) / "RunManifest.json").read_bytes())["run_id"]
    Record = {"at": time.time(), "event": Event, "run_id": RunId, **Fields}
    with (Path(Directory) / "Events.jsonl").open(
        "a", encoding="utf-8", newline="\n"
    ) as Output:
        Output.write(
            json.dumps(Record, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        )
        Output.flush()
        os.fsync(Output.fileno())
    return Record

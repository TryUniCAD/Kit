# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from json import loads as LoadJson
from time import time as UnixTime

from StoreRead import read_store as ReadStore


# queue snapshots include dependent zero attempt jobs that produce no wait settlement event
def FreezeState(StorePath):
    Database = StorePath.resolve() / "ledger.sqlite3"
    if Database.is_symlink() or not Database.is_file():
        raise ValueError("queue snapshot requires an initialized store")
    with ReadStore(Database, None, (4,)) as Connection:
        Through = Connection.execute(
            "SELECT COALESCE(MAX(id),0) FROM events"
        ).fetchone()[0]
        JobRows = Connection.execute(
            "SELECT id,kind,state,attempts,reason,definition_hash,definition,receipt,result FROM jobs ORDER BY id"
        ).fetchall()
        ObservedAt = UnixTime()
    Records = []
    for RowInfo in JobRows:
        Record = dict(RowInfo)
        Definition = LoadJson(Record.pop("definition"))
        Record["depends_on"] = Definition["depends_on"]
        Records.append(Record)
    return {
        "scope": "read_only_transactional_queue_observation",
        "observed_at": ObservedAt,
        "through_event_id": Through,
        "states": dict(sorted(Counter(Record["state"] for Record in Records).items())),
        "jobs": Records,
    }

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import time


# historical uncharged queue rows must not consume admission forever after their callers leave
def upgrade(db, version):
    if version not in (0, 1, 2):
        raise ValueError("unsupported shared advice database version")
    if version == 2:
        return
    db.execute(
        "ALTER TABLE requests ADD COLUMN charged INTEGER NOT NULL DEFAULT 0 CHECK(charged IN (0,1))"
    )
    db.execute(
        "UPDATE requests SET charged=1 WHERE state NOT IN ('queued','abandoned')"
    )
    db.execute("CREATE INDEX waiter_expiry ON waiters(until_at,provider,request_key)")
    db.execute("CREATE INDEX request_deadlines ON requests(provider,state,deadline)")
    now = time.time()
    db.execute("DELETE FROM waiters WHERE until_at<=?", (now,))
    db.execute(
        "DELETE FROM requests WHERE charged=0 AND state IN ('queued','abandoned') AND NOT EXISTS (SELECT 1 FROM waiters w WHERE w.provider=requests.provider AND w.request_key=requests.request_key AND w.until_at>?)",
        (now,),
    )
    db.execute(
        "CREATE TABLE advice_metadata (key TEXT PRIMARY KEY, value INTEGER NOT NULL CHECK(value>=0))"
    )
    db.execute(
        "INSERT INTO advice_metadata VALUES ('request_count',(SELECT COUNT(*) FROM requests))"
    )
    db.execute("PRAGMA user_version=2")

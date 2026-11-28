# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# live dependent counts make orphan decisions independent of a prerequisite's retained fanout
def install_demand(ledger):
    version = ledger.db.execute(
        "SELECT value FROM settings WHERE key='shared_queue_demand_version'"
    ).fetchone()
    if version is not None:
        if version[0] != 1:
            raise ValueError("unsupported shared queue demand extension")
        return
    statements = (
        "CREATE TABLE shared_demand (dependency TEXT PRIMARY KEY, live_children INTEGER NOT NULL CHECK(live_children>=0))",
        "INSERT INTO shared_demand SELECT d.dependency,COUNT(*) FROM dependencies d LEFT JOIN shared_cancelled c ON c.job_id=d.job_id WHERE c.job_id IS NULL GROUP BY d.dependency",
        "CREATE TRIGGER shared_demand_edge_added AFTER INSERT ON dependencies BEGIN INSERT INTO shared_demand VALUES (NEW.dependency,NOT EXISTS(SELECT 1 FROM shared_cancelled WHERE job_id=NEW.job_id)) ON CONFLICT(dependency) DO UPDATE SET live_children=live_children+excluded.live_children; END",
        "CREATE TRIGGER shared_demand_edge_removed AFTER DELETE ON dependencies WHEN NOT EXISTS(SELECT 1 FROM shared_cancelled WHERE job_id=OLD.job_id) BEGIN UPDATE shared_demand SET live_children=live_children-1 WHERE dependency=OLD.dependency; END",
        "CREATE TRIGGER shared_demand_edge_changed AFTER UPDATE ON dependencies BEGIN UPDATE shared_demand SET live_children=live_children-1 WHERE dependency=OLD.dependency AND NOT EXISTS(SELECT 1 FROM shared_cancelled WHERE job_id=OLD.job_id); INSERT INTO shared_demand VALUES (NEW.dependency,NOT EXISTS(SELECT 1 FROM shared_cancelled WHERE job_id=NEW.job_id)) ON CONFLICT(dependency) DO UPDATE SET live_children=live_children+excluded.live_children; END",
        "CREATE TRIGGER shared_demand_cancelled AFTER INSERT ON shared_cancelled BEGIN UPDATE shared_demand SET live_children=live_children-1 WHERE dependency IN (SELECT dependency FROM dependencies WHERE job_id=NEW.job_id); END",
        "CREATE TRIGGER shared_demand_restored AFTER DELETE ON shared_cancelled BEGIN INSERT INTO shared_demand SELECT dependency,1 FROM dependencies WHERE job_id=OLD.job_id ON CONFLICT(dependency) DO UPDATE SET live_children=live_children+1; END",
    )
    for statement in statements:
        ledger.db.execute(statement)
    ledger.db.execute("INSERT INTO settings VALUES ('shared_queue_demand_version',1)")

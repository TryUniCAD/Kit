# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# exact queue metadata remains cheap to poll even when retained history approaches its quota
def install_report(ledger):
    version = ledger.db.execute(
        "SELECT value FROM settings WHERE key='shared_queue_report_version'"
    ).fetchone()
    if version is not None:
        if version[0] != 1:
            raise ValueError("unsupported shared queue report extension")
        return
    for statement in (
        "CREATE TABLE shared_report_items (job_id TEXT PRIMARY KEY REFERENCES shared_jobs(job_id) ON DELETE CASCADE, state TEXT NOT NULL, created REAL NOT NULL, cancelled INTEGER NOT NULL CHECK(cancelled IN (0,1)), active_refs INTEGER NOT NULL CHECK(active_refs>=0))",
        "CREATE INDEX shared_report_oldest ON shared_report_items(created,job_id) WHERE cancelled=0 AND state='queued'",
        "CREATE TABLE shared_report_requests (request TEXT PRIMARY KEY REFERENCES shared_requests(request) ON DELETE CASCADE, job_count INTEGER NOT NULL CHECK(job_count>=0))",
        "CREATE TABLE shared_report_states (state TEXT PRIMARY KEY, count INTEGER NOT NULL CHECK(count>=0))",
        "CREATE TABLE shared_report_totals (name TEXT PRIMARY KEY, value INTEGER NOT NULL CHECK(value>=0))",
        "INSERT INTO shared_report_requests SELECT r.request,COUNT(m.local_id) FROM shared_requests r LEFT JOIN shared_members m ON m.request=r.request GROUP BY r.request",
        "INSERT INTO shared_report_items SELECT j.id,j.state,j.created,c.job_id IS NOT NULL,COALESCE(refs.count,0) FROM shared_jobs s JOIN jobs j ON j.id=s.job_id LEFT JOIN shared_cancelled c ON c.job_id=j.id LEFT JOIN (SELECT m.job_id,COUNT(*) AS count FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE r.active=1 GROUP BY m.job_id) refs ON refs.job_id=j.id",
        "INSERT INTO shared_report_states SELECT state,COUNT(*) FROM shared_report_items WHERE cancelled=0 GROUP BY state",
        "INSERT INTO shared_report_totals SELECT 'subscriptions',COALESCE(SUM(active_refs),0) FROM shared_report_items",
        "INSERT INTO shared_report_totals SELECT 'active_jobs',COALESCE(SUM(active_refs>0),0) FROM shared_report_items",
        "INSERT INTO shared_report_totals SELECT 'cancelled_jobs',COALESCE(SUM(cancelled),0) FROM shared_report_items",
    ):
        ledger.db.execute(statement)
    triggers = {
        "shared_report_item_added": "AFTER INSERT ON shared_report_items BEGIN INSERT OR IGNORE INTO shared_report_states VALUES (NEW.state,0); UPDATE shared_report_states SET count=count+(NEW.cancelled=0) WHERE state=NEW.state; UPDATE shared_report_totals SET value=value+NEW.active_refs WHERE name='subscriptions'; UPDATE shared_report_totals SET value=value+(NEW.active_refs>0) WHERE name='active_jobs'; UPDATE shared_report_totals SET value=value+NEW.cancelled WHERE name='cancelled_jobs'; END",
        "shared_report_item_removed": "AFTER DELETE ON shared_report_items BEGIN UPDATE shared_report_states SET count=count-(OLD.cancelled=0) WHERE state=OLD.state; UPDATE shared_report_totals SET value=value-OLD.active_refs WHERE name='subscriptions'; UPDATE shared_report_totals SET value=value-(OLD.active_refs>0) WHERE name='active_jobs'; UPDATE shared_report_totals SET value=value-OLD.cancelled WHERE name='cancelled_jobs'; END",
        "shared_report_item_state": "AFTER UPDATE OF state,cancelled ON shared_report_items WHEN OLD.state<>NEW.state OR OLD.cancelled<>NEW.cancelled BEGIN INSERT OR IGNORE INTO shared_report_states VALUES (NEW.state,0); UPDATE shared_report_states SET count=count-(OLD.cancelled=0) WHERE state=OLD.state; UPDATE shared_report_states SET count=count+(NEW.cancelled=0) WHERE state=NEW.state; UPDATE shared_report_totals SET value=value+NEW.cancelled-OLD.cancelled WHERE name='cancelled_jobs'; END",
        "shared_report_item_refs": "AFTER UPDATE OF active_refs ON shared_report_items WHEN OLD.active_refs<>NEW.active_refs BEGIN UPDATE shared_report_totals SET value=value+NEW.active_refs-OLD.active_refs WHERE name='subscriptions'; UPDATE shared_report_totals SET value=value+(NEW.active_refs>0)-(OLD.active_refs>0) WHERE name='active_jobs'; END",
        "shared_report_job_added": "AFTER INSERT ON shared_jobs BEGIN INSERT INTO shared_report_items SELECT NEW.job_id,j.state,j.created,EXISTS(SELECT 1 FROM shared_cancelled WHERE job_id=NEW.job_id),0 FROM jobs j WHERE j.id=NEW.job_id; END",
        "shared_report_job_state": "AFTER UPDATE OF state,created ON jobs BEGIN UPDATE shared_report_items SET state=NEW.state,created=NEW.created WHERE job_id=NEW.id; END",
        "shared_report_cancelled": "AFTER INSERT ON shared_cancelled BEGIN UPDATE shared_report_items SET cancelled=1 WHERE job_id=NEW.job_id; END",
        "shared_report_restored": "AFTER DELETE ON shared_cancelled BEGIN UPDATE shared_report_items SET cancelled=0 WHERE job_id=OLD.job_id; END",
        "shared_report_request_added": "AFTER INSERT ON shared_requests BEGIN INSERT INTO shared_report_requests VALUES (NEW.request,0); END",
        "shared_report_request_active": "AFTER UPDATE OF active ON shared_requests WHEN OLD.active<>NEW.active BEGIN UPDATE shared_report_items SET active_refs=active_refs+(NEW.active-OLD.active)*(SELECT COUNT(*) FROM shared_members m WHERE m.request=NEW.request AND m.job_id=shared_report_items.job_id) WHERE job_id IN (SELECT job_id FROM shared_members WHERE request=NEW.request); END",
        "shared_report_member_added": "AFTER INSERT ON shared_members BEGIN UPDATE shared_report_requests SET job_count=job_count+1 WHERE request=NEW.request; UPDATE shared_report_items SET active_refs=active_refs+(SELECT active FROM shared_requests WHERE request=NEW.request) WHERE job_id=NEW.job_id; END",
        "shared_report_member_removed": "AFTER DELETE ON shared_members BEGIN UPDATE shared_report_requests SET job_count=job_count-1 WHERE request=OLD.request; UPDATE shared_report_items SET active_refs=active_refs+(-1)*(SELECT active FROM shared_requests WHERE request=OLD.request) WHERE job_id=OLD.job_id; END",
    }
    for name, body in triggers.items():
        ledger.db.execute(f"CREATE TRIGGER {name} {body}")
    ledger.db.execute("INSERT INTO settings VALUES ('shared_queue_report_version',1)")

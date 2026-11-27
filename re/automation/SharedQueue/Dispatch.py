# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# mutation-time summaries let every claim seek a stable continuously aged ordering
def install_dispatch(ledger):
    version = ledger.db.execute(
        "SELECT value FROM settings WHERE key='shared_queue_dispatch_version'"
    ).fetchone()
    if version is not None:
        if version[0] != 1:
            raise ValueError("unsupported shared queue dispatch extension")
        return
    statements = (
        "CREATE TABLE shared_rank_votes (job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, priority INTEGER NOT NULL CHECK(priority BETWEEN 0 AND 100), refs INTEGER NOT NULL CHECK(refs>=0), PRIMARY KEY(job_id,priority DESC))",
        "CREATE TABLE shared_dispatch (job_id TEXT PRIMARY KEY REFERENCES jobs(id) ON DELETE CASCADE, state TEXT NOT NULL, kind TEXT NOT NULL, created REAL NOT NULL, priority INTEGER NOT NULL CHECK(priority BETWEEN 0 AND 100), rank REAL NOT NULL, pool TEXT)",
        "CREATE INDEX shared_dispatch_rank ON shared_dispatch(rank DESC,created,job_id) WHERE state='queued'",
        "CREATE INDEX shared_dispatch_pool ON shared_dispatch(pool,rank DESC,created,job_id) WHERE state='queued'",
        "CREATE INDEX shared_dispatch_kind ON shared_dispatch(kind)",
        "INSERT INTO shared_rank_votes SELECT m.job_id,r.priority,COUNT(*) FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE r.active=1 GROUP BY m.job_id,r.priority",
        "INSERT INTO shared_dispatch SELECT j.id,j.state,j.kind,j.created,COALESCE((SELECT v.priority FROM shared_rank_votes v WHERE v.job_id=j.id AND v.refs>0 ORDER BY v.priority DESC LIMIT 1),50),0,p.pool FROM jobs j LEFT JOIN pool_kinds p ON p.kind=j.kind",
        "UPDATE shared_dispatch SET rank=priority*60-created",
        "CREATE TRIGGER shared_dispatch_job_added AFTER INSERT ON jobs BEGIN INSERT INTO shared_dispatch VALUES (NEW.id,NEW.state,NEW.kind,NEW.created,50,3000-NEW.created,(SELECT pool FROM pool_kinds WHERE kind=NEW.kind)); END",
        "CREATE TRIGGER shared_dispatch_job_changed AFTER UPDATE OF state,kind,created ON jobs BEGIN UPDATE shared_dispatch SET state=NEW.state,kind=NEW.kind,created=NEW.created,rank=priority*60-NEW.created,pool=(SELECT pool FROM pool_kinds WHERE kind=NEW.kind) WHERE job_id=NEW.id; END",
        "CREATE TRIGGER shared_dispatch_pool_added AFTER INSERT ON pool_kinds BEGIN UPDATE shared_dispatch SET pool=NEW.pool WHERE kind=NEW.kind; END",
        "CREATE TRIGGER shared_dispatch_pool_removed AFTER DELETE ON pool_kinds BEGIN UPDATE shared_dispatch SET pool=NULL WHERE kind=OLD.kind; END",
        "CREATE TRIGGER shared_dispatch_pool_changed AFTER UPDATE ON pool_kinds BEGIN UPDATE shared_dispatch SET pool=(SELECT pool FROM pool_kinds WHERE kind=shared_dispatch.kind) WHERE kind IN (OLD.kind,NEW.kind); END",
        "CREATE TRIGGER shared_rank_member_added AFTER INSERT ON shared_members WHEN (SELECT active FROM shared_requests WHERE request=NEW.request)=1 BEGIN INSERT INTO shared_rank_votes VALUES (NEW.job_id,(SELECT priority FROM shared_requests WHERE request=NEW.request),1) ON CONFLICT(job_id,priority) DO UPDATE SET refs=refs+1; END",
        "CREATE TRIGGER shared_rank_member_removed AFTER DELETE ON shared_members WHEN (SELECT active FROM shared_requests WHERE request=OLD.request)=1 BEGIN UPDATE shared_rank_votes SET refs=refs-1 WHERE job_id=OLD.job_id AND priority=(SELECT priority FROM shared_requests WHERE request=OLD.request); END",
        "CREATE TRIGGER shared_rank_request_changed AFTER UPDATE OF active,priority ON shared_requests WHEN OLD.active<>NEW.active OR OLD.priority<>NEW.priority BEGIN UPDATE shared_rank_votes SET refs=refs-(SELECT COUNT(*) FROM shared_members m WHERE m.request=NEW.request AND m.job_id=shared_rank_votes.job_id) WHERE OLD.active=1 AND priority=OLD.priority AND job_id IN (SELECT job_id FROM shared_members WHERE request=NEW.request); INSERT INTO shared_rank_votes SELECT job_id,NEW.priority,COUNT(*) FROM shared_members WHERE request=NEW.request AND NEW.active=1 GROUP BY job_id ON CONFLICT(job_id,priority) DO UPDATE SET refs=refs+excluded.refs; END",
    )
    for statement in statements:
        ledger.db.execute(statement)
    for action, source in (
        ("INSERT", "NEW"),
        ("UPDATE OF refs", "NEW"),
        ("DELETE", "OLD"),
    ):
        name = action.split()[0].lower()
        ledger.db.execute(
            f"CREATE TRIGGER shared_rank_votes_{name} AFTER {action} ON shared_rank_votes BEGIN UPDATE shared_dispatch SET priority=COALESCE((SELECT priority FROM shared_rank_votes WHERE job_id={source}.job_id AND refs>0 ORDER BY priority DESC LIMIT 1),50) WHERE job_id={source}.job_id; UPDATE shared_dispatch SET rank=priority*60-created WHERE job_id={source}.job_id; END"
        )
    ledger.db.execute("INSERT INTO settings VALUES ('shared_queue_dispatch_version',1)")


# pool-specific indexes avoid walking another application's blocked backlog before ready work
def dispatch_query(pool):
    index = "shared_dispatch_rank" if pool is None else "shared_dispatch_pool"
    scope = "" if pool is None else " AND dispatch.pool=:pool"
    return (
        f"shared_dispatch dispatch INDEXED BY {index} CROSS JOIN jobs j ON j.id=dispatch.job_id ",
        " AND dispatch.state='queued'" + scope,
        "dispatch.rank DESC,dispatch.created,dispatch.job_id",
    )

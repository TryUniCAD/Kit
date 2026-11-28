# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import math
import os
import re
import sqlite3
import stat
import time
from contextlib import contextmanager
from pathlib import Path

from CodexAdvice.SharedSchema import upgrade
from Records import bounded, canonical


# independent research processes need one durable owner private provider allowance
class SharedBudget:
    def __init__(self, directory, provider, limit=None, parallel=None):
        if provider not in {"codex", "claude", "ollama"}:
            raise ValueError("unsupported shared advice provider")
        self.provider = provider
        self.limit = None if limit is None else bounded(limit, 1, 10000)
        self.parallel = None if parallel is None else bounded(parallel, 1, 16)
        self.root = Path(directory).absolute()
        if os.name != "posix":
            raise ValueError(
                "shared advice requires an owner-private local POSIX directory"
            )
        if self.root.is_symlink():
            raise ValueError("shared advice directory cannot be a symbolic link")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.root.lstat()
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            raise ValueError("shared advice directory must be owner-private")
        self.root = self.root.resolve()
        database = self.root / "Advice.sqlite3"
        if database.exists() or database.is_symlink():
            info = database.lstat()
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
            ):
                raise ValueError(
                    "shared advice database must be owner-private and regular"
                )
        else:
            try:
                descriptor = os.open(
                    database, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
                )
            except FileExistsError:
                info = database.lstat()
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.getuid()
                    or info.st_mode & 0o077
                ):
                    raise ValueError(
                        "shared advice database must be owner-private and regular"
                    )
            else:
                os.close(descriptor)
        self.db = sqlite3.connect(database, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.waiting = {}
        try:
            self.db.execute("PRAGMA synchronous=FULL")
            if self.db.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
                self.db.execute("PRAGMA journal_mode=DELETE")
            if self.db.execute("PRAGMA user_version").fetchone()[0] == 2:
                config = self.db.execute(
                    "SELECT call_limit,parallel FROM providers WHERE name=?",
                    (provider,),
                ).fetchone()
                if config is not None:
                    self.configure(config)
                    return
            with self.transaction():
                version = self.db.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if self.db.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table'"
                    ).fetchone():
                        raise ValueError("unrecognized shared advice database")
                    self.db.execute(
                        "CREATE TABLE providers (name TEXT PRIMARY KEY, call_limit INTEGER NOT NULL, parallel INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)"
                    )
                    self.db.execute(
                        "CREATE TABLE requests (provider TEXT NOT NULL, request_key TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('queued','running','uncertain','done','failed','abandoned')), created REAL NOT NULL, deadline REAL, owner TEXT, proposal TEXT, attempts TEXT, PRIMARY KEY(provider,request_key))"
                    )
                    self.db.execute(
                        "CREATE INDEX request_queue ON requests(provider,state,created,request_key)"
                    )
                    self.db.execute(
                        "CREATE TABLE waiters (provider TEXT NOT NULL, request_key TEXT NOT NULL, token TEXT NOT NULL PRIMARY KEY, until_at REAL NOT NULL)"
                    )
                    self.db.execute(
                        "CREATE INDEX request_waiters ON waiters(provider,request_key,until_at)"
                    )
                    self.db.execute("PRAGMA user_version=1")
                upgrade(self.db, version)
                self.db.execute(
                    "INSERT OR IGNORE INTO providers(name,call_limit,parallel) VALUES (?,?,?)",
                    (
                        provider,
                        self.limit if self.limit is not None else 16,
                        self.parallel if self.parallel is not None else 1,
                    ),
                )
                config = self.db.execute(
                    "SELECT call_limit,parallel FROM providers WHERE name=?",
                    (provider,),
                ).fetchone()
                self.configure(config)
        except BaseException:
            self.db.close()
            raise

    # reopening an initialized provider must validate its fixed limits without taking the writer lock
    def configure(self, config):
        if (self.limit is not None and config["call_limit"] != self.limit) or (
            self.parallel is not None and config["parallel"] != self.parallel
        ):
            raise ValueError(
                "shared advice limits differ from the existing provider configuration"
            )
        self.limit, self.parallel = config["call_limit"], config["parallel"]

    # idle observations must release their read snapshot before the caller waits
    @contextmanager
    def snapshot(self):
        self.db.execute("BEGIN")
        try:
            yield
        finally:
            self.db.execute("ROLLBACK")

    # reservations must commit before provider calls without holding a database lock during inference
    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    # closing a caller must never silently release an uncertain external request
    def close(self):
        self.db.close()

    # expiry keys keep ordinary polling independent of terminal provider history
    def sweep(self, now):
        expired = self.db.execute(
            "SELECT provider,request_key,token FROM waiters WHERE until_at<=? "
            "ORDER BY until_at,provider,request_key LIMIT 256",
            (now,),
        ).fetchall()
        self.db.executemany(
            "DELETE FROM waiters WHERE token=? AND until_at<=?",
            [(row["token"], now) for row in expired],
        )
        for provider, key in {(row["provider"], row["request_key"]) for row in expired}:
            self.prune(key, now, provider)
        self.db.execute(
            "UPDATE requests SET state='uncertain' WHERE provider=? AND state='running' AND deadline<=?",
            (self.provider, now),
        )

    # a bounded cleanup batch must not strand admission behind expired charged waiters
    def reclaim(self, now):
        row = self.db.execute(
            "SELECT w.provider,w.request_key FROM waiters w INDEXED BY waiter_expiry "
            "CROSS JOIN requests r WHERE w.until_at<=? "
            "AND r.provider=w.provider AND r.request_key=w.request_key "
            "AND r.charged=0 AND r.state IN ('queued','abandoned') "
            "AND NOT EXISTS (SELECT 1 FROM waiters live WHERE live.provider=w.provider "
            "AND live.request_key=w.request_key AND live.until_at>?) LIMIT 1",
            (now, now),
        ).fetchone()
        if row is not None:
            self.prune(row["request_key"], now, row["provider"])

    # charged outcomes remain immutable history even after every interested caller leaves
    def prune(self, key, now, provider=None):
        provider = self.provider if provider is None else provider
        deleted = self.db.execute(
            "DELETE FROM requests WHERE provider=? AND request_key=? AND charged=0 "
            "AND state IN ('queued','abandoned') AND NOT EXISTS ("
            "SELECT 1 FROM waiters w WHERE w.provider=requests.provider "
            "AND w.request_key=requests.request_key AND w.until_at>?)",
            (provider, key, now),
        ).rowcount
        if deleted:
            self.db.execute(
                "DELETE FROM waiters WHERE provider=? AND request_key=? AND until_at<=?",
                (provider, key, now),
            )
            self.db.execute(
                "UPDATE advice_metadata SET value=value-? WHERE key='request_count'",
                (deleted,),
            )

    # admission cost must stay constant when paid request history grows
    def request_count(self):
        row = self.db.execute(
            "SELECT value FROM advice_metadata WHERE key='request_count'"
        ).fetchone()
        if row is None or type(row[0]) is not int or row[0] < 0:
            raise ValueError("invalid shared advice metadata count")
        return row[0]

    # duplicate observers must not acquire the database writer lock or renew waiter leases while idle
    def reserve(self, key, token, seconds, *, wait_until=None):
        if not re.fullmatch("[0-9a-f]{64}", key) or not re.fullmatch(
            "[0-9a-f]{64}", token
        ):
            raise ValueError("invalid shared advice request identity")
        if not 1 <= seconds <= 180:
            raise ValueError("shared advice attempts must take 1 to 180 seconds")
        now = time.time()
        previous = self.waiting.get(token)
        if wait_until is None:
            wait_until = previous[1] if previous is not None else now + seconds
        if type(wait_until) not in (int, float) or not math.isfinite(wait_until):
            raise ValueError("invalid shared advice waiting deadline")
        if previous is not None and previous[:2] != (key, wait_until):
            raise ValueError("shared advice waiter identity or deadline changed")
        if wait_until <= now:
            return {"status": "wait_expired"}
        self.waiting.setdefault(token, (key, wait_until, False))
        with self.snapshot():
            decision = self.observe(key, token, now)
        return (
            self.acquire(key, token, seconds, wait_until)
            if decision is None
            else decision
        )

    # terminal cached advice retains its original scope without any new reservation
    def terminal(self, row):
        return {
            "status": (
                "cached"
                if row["state"] == "done"
                else "prior_failure" if row["state"] == "failed" else "uncertain"
            ),
            "proposal": json.loads(row["proposal"]) if row["proposal"] else None,
        }

    # read snapshots separate an idle observer from a contender that needs atomic admission
    def observe(self, key, token, now):
        row = self.db.execute(
            "SELECT * FROM requests WHERE provider=? AND request_key=?",
            (self.provider, key),
        ).fetchone()
        if row is not None and row["state"] in {"done", "failed", "uncertain"}:
            return self.terminal(row)
        waiter = self.db.execute(
            "SELECT provider,request_key,until_at FROM waiters WHERE token=?", (token,)
        ).fetchone()
        if waiter is None:
            return {"status": "wait_expired"} if self.waiting[token][2] else None
        if (waiter["provider"], waiter["request_key"], waiter["until_at"]) != (
            self.provider,
            key,
            self.waiting[token][1],
        ):
            raise ValueError("shared advice waiter identity or deadline changed")
        if waiter["until_at"] <= now:
            return {"status": "wait_expired"}
        self.waiting[token] = (key, waiter["until_at"], True)
        config = self.db.execute(
            "SELECT used,call_limit,parallel FROM providers WHERE name=?",
            (self.provider,),
        ).fetchone()
        if (
            self.db.execute(
                "SELECT 1 FROM waiters WHERE until_at<=? LIMIT 1", (now,)
            ).fetchone()
            is not None
            or self.db.execute(
                "SELECT 1 FROM requests WHERE provider=? AND state='running' AND deadline<=? LIMIT 1",
                (self.provider, now),
            ).fetchone()
            is not None
        ):
            return None
        if row is not None and row["state"] == "running":
            return {"status": "waiting"}
        if config["used"] >= config["call_limit"]:
            return {"status": "budget_exhausted"}
        active = self.db.execute(
            "SELECT COUNT(*) FROM requests WHERE provider=? AND state IN ('running','uncertain')",
            (self.provider,),
        ).fetchone()[0]
        if active >= config["parallel"]:
            return {"status": "waiting"}
        first = self.db.execute(
            "SELECT request_key FROM requests r WHERE provider=? AND state='queued' AND EXISTS (SELECT 1 FROM waiters w WHERE w.provider=r.provider AND w.request_key=r.request_key AND w.until_at>?) ORDER BY created,request_key LIMIT 1",
            (self.provider, now),
        ).fetchone()
        return None if first is not None and first[0] == key else {"status": "waiting"}

    # only a new join or potentially eligible acquisition may enter the durable writer path
    def acquire(self, key, token, seconds, wait_until):
        with self.transaction():
            now = time.time()
            if wait_until <= now:
                return {"status": "wait_expired"}
            self.sweep(now)
            row = self.db.execute(
                "SELECT * FROM requests WHERE provider=? AND request_key=?",
                (self.provider, key),
            ).fetchone()
            if row is not None and row["state"] in {"done", "failed", "uncertain"}:
                return self.terminal(row)
            if row is None:
                if self.request_count() >= 10000:
                    self.reclaim(now)
                if self.request_count() >= 10000:
                    return {"status": "metadata_limit"}
                self.db.execute(
                    "INSERT INTO requests(provider,request_key,state,created) VALUES (?,?,'queued',?)",
                    (self.provider, key, now),
                )
                self.db.execute(
                    "UPDATE advice_metadata SET value=value+1 WHERE key='request_count'"
                )
            elif row["state"] == "abandoned":
                self.db.execute(
                    "UPDATE requests SET state='queued',created=? WHERE provider=? AND request_key=?",
                    (now, self.provider, key),
                )
            existing = self.db.execute(
                "SELECT provider,request_key,until_at FROM waiters WHERE token=?",
                (token,),
            ).fetchone()
            if existing is not None and (
                existing["provider"],
                existing["request_key"],
                existing["until_at"],
            ) != (self.provider, key, wait_until):
                raise ValueError("shared advice waiter identity or deadline changed")
            if existing is None:
                if self.waiting[token][2]:
                    return {"status": "wait_expired"}
                self.db.execute(
                    "INSERT INTO waiters VALUES (?,?,?,?)",
                    (self.provider, key, token, wait_until),
                )
            self.waiting[token] = (key, wait_until, True)
            if row is not None and row["state"] == "running":
                return {"status": "waiting"}
            config = self.db.execute(
                "SELECT * FROM providers WHERE name=?", (self.provider,)
            ).fetchone()
            if config["used"] >= config["call_limit"]:
                return {"status": "budget_exhausted"}
            active = self.db.execute(
                "SELECT COUNT(*) FROM requests WHERE provider=? AND state IN ('running','uncertain')",
                (self.provider,),
            ).fetchone()[0]
            first = self.db.execute(
                "SELECT request_key FROM requests r WHERE provider=? AND state='queued' "
                "AND EXISTS (SELECT 1 FROM waiters w WHERE w.provider=r.provider "
                "AND w.request_key=r.request_key AND w.until_at>?) "
                "ORDER BY created,request_key LIMIT 1",
                (self.provider, now),
            ).fetchone()
            if active >= config["parallel"] or first[0] != key:
                return {"status": "waiting"}
            now = time.time()
            if wait_until <= now:
                return {"status": "wait_expired"}
            self.db.execute(
                "UPDATE providers SET used=used+1 WHERE name=?", (self.provider,)
            )
            self.db.execute(
                "UPDATE requests SET state='running',charged=1,owner=?,deadline=? WHERE provider=? AND request_key=?",
                (token, now + seconds + 30, self.provider, key),
            )
            self.db.execute("DELETE FROM waiters WHERE token=?", (token,))
            return {"status": "reserved"}

    # a result can replace only the exact reservation that dispatched its provider call
    def finish(self, key, token, proposal, attempts, *, uncertain=False):
        encoded = canonical(proposal) if proposal is not None else None
        history = canonical(attempts)
        if (encoded is not None and len(encoded.encode("utf-8")) > 8192) or len(
            history.encode("utf-8")
        ) > 8192:
            raise ValueError("shared advice result exceeds its bounded record size")
        with self.transaction():
            changed = self.db.execute(
                "UPDATE requests SET state=?,proposal=?,attempts=?,owner=NULL,deadline=NULL WHERE provider=? AND request_key=? AND owner=? AND state IN ('running','uncertain')",
                (
                    (
                        "uncertain"
                        if uncertain
                        else "done" if proposal is not None else "failed"
                    ),
                    encoded,
                    history,
                    self.provider,
                    key,
                    token,
                ),
            ).rowcount
            if changed != 1:
                raise ValueError("shared advice reservation was replaced")

    # leaving the queue releases only this waiter and never another callers active request
    def leave(self, token):
        self.waiting.pop(token, None)
        with self.snapshot():
            present = self.db.execute(
                "SELECT 1 FROM waiters WHERE provider=? AND token=?",
                (self.provider, token),
            ).fetchone()
        if present is None:
            return
        with self.transaction():
            row = self.db.execute(
                "SELECT request_key FROM waiters WHERE provider=? AND token=?",
                (self.provider, token),
            ).fetchone()
            self.db.execute(
                "DELETE FROM waiters WHERE provider=? AND token=?",
                (self.provider, token),
            )
            now = time.time()
            self.sweep(now)
            if row is not None:
                self.prune(row[0], now)

    # operational reports expose consumption and unresolved reservations without provider secrets
    def status(self):
        with self.transaction():
            self.sweep(time.time())
            providers = [
                dict(row)
                for row in self.db.execute("SELECT * FROM providers ORDER BY name")
            ]
            counts = [
                dict(row)
                for row in self.db.execute(
                    "SELECT provider,state,COUNT(*) AS count FROM requests GROUP BY provider,state ORDER BY provider,state"
                )
            ]
            pending = [
                dict(row)
                for row in self.db.execute(
                    "SELECT provider,request_key,state,created,deadline FROM requests WHERE state IN ('running','uncertain') ORDER BY created LIMIT 100"
                )
            ]
            return {
                "shared_advice_version": 1,
                "providers": providers,
                "counts": counts,
                "reservations": pending,
            }

    # an operator must confirm external work stopped before a crashed reservation frees capacity
    def recover(self, key):
        if not re.fullmatch("[0-9a-f]{64}", key):
            raise ValueError("invalid shared advice request identity")
        with self.transaction():
            changed = self.db.execute(
                "UPDATE requests SET state='failed',owner=NULL,deadline=NULL WHERE provider=? AND request_key=? AND state IN ('running','uncertain')",
                (self.provider, key),
            ).rowcount
            if changed != 1:
                raise ValueError("request has no running or uncertain reservation")
            return {"status": "recovered", "request_key": key, "budget_refunded": False}

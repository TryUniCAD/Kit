# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from contextlib import contextmanager
from json import loads as DecodeJson
from sqlite3 import Error as DatabaseError
from sys import stderr
from threading import Event, Thread

from StoreRead import read_store


# progress observes the private ledger without acquiring a write transaction
def ReadJobCounts(Directory):
    with read_store(
        Directory / "Store" / "ledger.sqlite3", None, (4,), timeout=0.1
    ) as State:
        return Counter(
            {
                Row["state"]: Row["total"]
                for Row in State.execute(
                    "SELECT state, COUNT(*) AS total FROM jobs GROUP BY state"
                )
            }
        )


# event accounting counts worker processes separately from their claimed jobs
class CatalogueProgress:
    def __init__(self, Directory, LogPath, Offset):
        self.Directory = Directory
        self.LogPath = LogPath
        self.Offset = Offset
        self.Sessions = set()
        self.Blockers = {}
        self.Previous = None
        self.Paused = False

    def ReadEvents(self):
        with self.LogPath.open("rb") as Stream:
            _ = Stream.seek(self.Offset)
            while Line := Stream.readline():
                if not Line.endswith(b"\n"):
                    break
                self.Offset = Stream.tell()
                try:
                    Record = DecodeJson(Line)
                except (ValueError, UnicodeError):
                    continue
                if isinstance(Record, dict):
                    self.Apply(Record)

    def Apply(self, Record):
        KindName = Record.get("event")
        if KindName == "started":
            self.Sessions.add(Record["session"])
            self.Blockers.pop(Record.get("pool"), None)
        elif KindName == "finished":
            self.Sessions.discard(Record["session"])
        elif KindName == "admission" and Record.get("pool"):
            self.Blockers[Record["pool"]] = Record.get("reason")
        elif KindName == "controller_claim_refused" and Record.get("pool"):
            self.Blockers[Record["pool"]] = Record.get("reason")
        elif KindName == "catalogue_paused":
            self.Paused = True

    def Report(self):
        try:
            self.ReadEvents()
            Counts = ReadJobCounts(self.Directory)
        except (ValueError, OSError, DatabaseError):
            return
        Parts = [
            f"{len(self.Sessions)} workers active",
            f"{Counts['queued']} queued",
            f"{Counts['completed']} completed",
        ]
        for StateName, Description in (
            ("waiting_application", "waiting for a CAD session"),
            ("waiting_evidence", "waiting for evidence"),
            ("waiting_ci", "waiting for CI"),
        ):
            if Counts[StateName]:
                Parts.append(f"{Counts[StateName]} {Description}")
        if self.Paused:
            Parts.append("paused for new work")
        elif Counts["queued"] and not self.Sessions:
            Reasons = {
                "memory headroom": "RAM below reserve or worker requirement",
                "cpu headroom": "CPU below worker requirement",
                "adaptive limit": "worker limit adjusting to resources",
            }
            Parts.extend(
                sorted(
                    {
                        Reasons.get(Value, Value)
                        for Value in self.Blockers.values()
                        if Value
                    }
                )
            )
        Status = " | ".join(Parts)
        if Status != self.Previous:
            try:
                print(f"kit: {Status}", file=stderr, flush=True)
            except OSError:
                return
            self.Previous = Status

    def Observe(self, StopEvent):
        while not StopEvent.wait(1):
            self.Report()


# structured reports and event logs remain usable while terminal progress goes to stderr
@contextmanager
def ObserveCatalogue(Directory, LogPath, Offset):
    Progress = CatalogueProgress(Directory, LogPath, Offset)
    StopEvent = Event()
    Worker = Thread(target=Progress.Observe, args=(StopEvent,), daemon=True)
    Progress.Report()
    Worker.start()
    try:
        yield
    finally:
        StopEvent.set()
        Worker.join()
        Progress.Report()

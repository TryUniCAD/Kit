# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from csv import writer
from hashlib import sha256
from sqlite3 import connect

from CatalogRows import JsonText
from CatalogSchema import KSchema


# stable insertion order makes sqlite artifacts repeatable on one sqlite version
def WriteDatabase(Rows, Target):
    Database = connect(Target)
    try:
        Database.executescript(KSchema)
        with Database:
            for Table, Registry in (
                ("sources", Rows.Sources),
                ("items", Rows.Items),
                ("relations", Rows.Relations),
                ("gaps", Rows.Gaps),
            ):
                Records = [Registry[Identity] for Identity in sorted(Registry)]
                if Records:
                    Marks = ",".join("?" for Value in Records[0])
                    Database.executemany(
                        "INSERT INTO " + Table + " VALUES (" + Marks + ")", Records
                    )
        if (
            Database.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
            or Database.execute("PRAGMA foreign_key_check").fetchall()
        ):
            raise ValueError("Invalid generated database")
    finally:
        Database.close()


# logical fingerprints distinguish record equivalence from sqlite storage layout changes
def ReadSummary(Database):
    Digest = sha256()
    Counts = {}
    for Table in ("sources", "items", "relations", "gaps"):
        Records = Database.execute("SELECT * FROM " + Table + " ORDER BY id")
        Counts[Table] = 0
        Digest.update((Table + "\n").encode())
        for Record in Records:
            Digest.update((JsonText(Record) + "\n").encode())
            Counts[Table] += 1
    Counts["item_kinds"] = dict(
        Database.execute("SELECT kind,count(*) FROM items GROUP BY kind ORDER BY kind")
    )
    return Counts, Digest.hexdigest()


# csv slices remain directly usable without vendor software or database tooling
def WriteExport(Database, ViewName, Target):
    KnownViews = {
        Record[0]
        for Record in Database.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
        )
    }
    if ViewName not in KnownViews:
        raise ValueError("Unknown export view")
    Records = Database.execute('SELECT * FROM "' + ViewName + '" ORDER BY id')
    Count = 0
    with Target.open("x", encoding="utf-8", newline="") as Output:
        Writer = writer(Output, lineterminator="\n")
        Writer.writerow([Column[0] for Column in Records.description])
        for Record in Records:
            Writer.writerow(Record)
            Count += 1
    return Count

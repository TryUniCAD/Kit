# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from contextlib import AbstractContextManager
from importlib import import_module as ImportModule
from sqlite3 import Connection
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath

from tests.Research.Inference.Authoring.Contracts.ReadText import ReadText

# dynamic research imports retain their runtime location without widening static analysis scope
KSubmitSolid = CastValue(
    Callable[[FilePath, object, str], list[dict[str, object]]],
    getattr(ImportModule("InferenceGrid.Authoring.SubmitSolid"), "SubmitSolid"),
)

# the real controller store remains owned by the context that originally acquired it
KLedger = CastValue(
    Callable[[FilePath, bool], AbstractContextManager[object]],
    getattr(ImportModule("Ledger"), "Ledger"),
)


# real controller submissions must amortize only new recipe captures while retaining one decoder per case
def SubmitPlan(Payload: dict[str, object]) -> dict[str, object]:
    Directory = FilePath(ReadText(Payload["directory"]))
    Directory.mkdir(exist_ok=True)
    PlanValue = DecodeJson(FilePath(ReadText(Payload["plan"])).read_bytes())
    with KLedger(Directory / "Store", True) as State:
        ResourceCall = CastValue(
            Callable[[str, bool, int], object], getattr(State, "resource")
        )
        _ = ResourceCall("native.solidworks", False, 1)
    Submissions = KSubmitSolid(Directory, PlanValue, "native.solidworks")
    with KLedger(Directory / "Store", False) as State:
        StatusCall = CastValue(
            Callable[[], dict[str, object]], getattr(State, "status")
        )
        Status = StatusCall()
        Database = CastValue(Connection, getattr(State, "db"))
        ObjectPath = CastValue(
            Callable[[str], FilePath], getattr(getattr(State, "objects"), "path")
        )
        Definitions = [
            DecodeJson(Entry[0])
            for Entry in Database.execute("SELECT definition FROM jobs ORDER BY id")
        ]
        Bindings = [
            {
                **dict(Entry),
                "record": DecodeJson(ObjectPath(Entry["sha256"]).read_bytes()),
            }
            for Entry in Database.execute("SELECT * FROM bindings ORDER BY name")
        ]
    return {
        "submissions": Submissions,
        "status": Status,
        "definitions": Definitions,
        "bindings": Bindings,
    }

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from InferenceGrid.Authoring.SubmitSolid import SubmitSolid
from Ledger import Ledger


# real controller submissions must amortize only new recipe captures while retaining one decoder per case
def SubmitPlan(Payload: dict) -> dict:
    Directory = FilePath(Payload["directory"])
    Directory.mkdir(exist_ok=True)
    PlanValue = DecodeJson(FilePath(Payload["plan"]).read_bytes())
    with Ledger(Directory / "Store", create=True) as State:
        _ = State.resource("native.solidworks", False, 1)
    Submissions = SubmitSolid(Directory, PlanValue, "native.solidworks")
    with Ledger(Directory / "Store") as State:
        Status = State.status()
        Definitions = [
            DecodeJson(Entry[0])
            for Entry in State.db.execute("SELECT definition FROM jobs ORDER BY id")
        ]
        Bindings = [
            {
                **dict(Entry),
                "record": DecodeJson(State.objects.path(Entry["sha256"]).read_bytes()),
            }
            for Entry in State.db.execute("SELECT * FROM bindings ORDER BY name")
        ]
    return {
        "submissions": Submissions,
        "status": Status,
        "definitions": Definitions,
        "bindings": Bindings,
    }

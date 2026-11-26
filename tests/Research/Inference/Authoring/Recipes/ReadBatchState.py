# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from typing import cast as CastValue
from tests.Research.Inference.Authoring.Contracts.OutcomeData import OutcomeData
from pathlib import Path as FilePath

from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe


# actual completed fixture jobs must retain their separate decoder statuses without creating native proof counts
def ReadBatchState(TmpPath: FilePath) -> OutcomeData:
    Samples: dict[str, object] = {}
    Features: dict[str, object] = {}
    Submissions: list[dict[str, object]] = []
    for Label in ("first", "second"):
        Identity = "fusion:" + Label
        Samples[Identity] = {
            "case": {"id": Label, "recipe": "fixture", "parameters": {}, "options": {}}
        }
        Features[Label] = {"status": "planned", "samples": [Identity]}
        Submissions.append(
            {
                "samples": [Identity],
                "capture": ["fixture-native"],
                "decode": "decode-" + Label,
            }
        )
    Features["unregistered"] = {"status": "authoring_recipe_unavailable"}
    PlanValue = {
        "inputs_sha256": "fixture-only-transport-plan",
        "features": {"fusion": Features},
        "samples": Samples,
    }
    Process = RunProbe(
        TmpPath,
        "outcome",
        {"directory": str(TmpPath), "plan": PlanValue, "submissions": Submissions},
    )
    assert Process.returncode == 0, Process.stderr
    return CastValue(OutcomeData, DecodeJson(Process.stdout))

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths

# the probe exercises orchestration against the same checkout as its controller receipts
KRepoRoot = FilePath(__file__).resolve().parents[4]
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))

from InferenceGrid.BuilderDevelopment.StageState import DevelopmentStopped, StageState


# recovery must reuse accepted controller results without inventing another execution
def ProbeStage() -> int:
    RunPath = FilePath(ArgValues[1])
    JobValue = DecodeJson((RunPath / "BuilderJob.json").read_bytes())
    StateValue = DecodeJson((RunPath / "BuilderState.json").read_bytes())
    StateValue["recovery_epoch"] = int(ArgValues[2])
    Context = StageState(
        RunPath, KRepoRoot, JobValue, StateValue, RunPath / "Supervisor.json"
    )
    Context.Save()
    try:
        Identity, Records, ResultInfo = Context.Stage(
            "fixture.stage", "verify", {"fixture_only": True}
        )
    except DevelopmentStopped as ErrorInfo:
        print(EncodeJson({"classification": ErrorInfo.classification}))
        return 3
    print(
        EncodeJson(
            {"id": Identity, "records": Records, "receipt": ResultInfo["receipt"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(ProbeStage())

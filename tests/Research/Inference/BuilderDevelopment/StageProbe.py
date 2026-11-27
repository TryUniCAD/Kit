# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from json import dumps as EncodeJson, loads as DecodeJson
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths

# the probe exercises orchestration against the same checkout as its controller receipts
KRepoRoot = FilePath(__file__).resolve().parents[4]

SearchPaths.insert(0, str(KRepoRoot))
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))


# recovery must reuse accepted controller results without inventing another execution
def ProbeStage() -> int:
    StateModule = ImportModule("InferenceGrid.BuilderDevelopment.StageState")
    StateMaker = CastValue(
        Callable[
            [FilePath, FilePath, dict[str, object], dict[str, object], FilePath], object
        ],
        StateModule.StageState,
    )
    StoppedError = CastValue(type[Exception], StateModule.DevelopmentStopped)
    RunPath = ResolveTemp(ArgValues[1])
    JobValue = DecodeJson((RunPath / "BuilderJob.json").read_bytes())
    StateValue = DecodeJson((RunPath / "BuilderState.json").read_bytes())
    StateValue["recovery_epoch"] = int(ArgValues[2])
    Context = StateMaker(
        RunPath, KRepoRoot, JobValue, StateValue, RunPath / "Supervisor.json"
    )
    SaveContext = CastValue(Callable[[], None], getattr(Context, "Save"))
    SaveContext()
    StageCall = CastValue(
        Callable[
            [str, str, dict[str, object]],
            tuple[str, dict[str, object], dict[str, object]],
        ],
        getattr(Context, "Stage"),
    )
    try:
        Identity, Records, ResultInfo = StageCall(
            "fixture.stage", "verify", {"fixture_only": True}
        )
    except StoppedError as ErrorInfo:
        print(
            EncodeJson(
                {"classification": CastValue(str, getattr(ErrorInfo, "classification"))}
            )
        )
        return 3
    print(
        EncodeJson(
            {"id": Identity, "records": Records, "receipt": ResultInfo["receipt"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(ProbeStage())

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths

# qualification orchestration must consume real controller state from the tested checkout
KRepoRoot = FilePath(__file__).resolve().parents[4]

SearchPaths.insert(0, str(KRepoRoot))
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))


# rejected native fixtures expose retirement behavior while never establishing acceptance
def ProbeReserve() -> int:
    StateModule = ImportModule("InferenceGrid.BuilderDevelopment.StageState")
    StateMaker = CastValue(
        Callable[
            [FilePath, FilePath, dict[str, object], dict[str, object], FilePath], object
        ],
        StateModule.StageState,
    )
    StoppedError = CastValue(type[Exception], StateModule.DevelopmentStopped)
    RecordDigest = CastValue(Callable[[object], str], ImportModule("Records").digest)
    QualifyCall = CastValue(
        Callable[[object, dict[str, object]], object],
        ImportModule(
            "InferenceGrid.BuilderDevelopment.DevelopCandidate"
        ).QualifyAttempt,
    )
    RunPath = FilePath(ArgValues[1])
    JobValue = DecodeJson((RunPath / "BuilderJob.json").read_bytes())
    StateValue = DecodeJson((RunPath / "BuilderState.json").read_bytes())
    NumberValue = int(ArgValues[2])
    if len(StateValue["attempts"]) < NumberValue:
        Candidate = {
            "schema": 1,
            "operation": "offset_plane",
            "support": "XY",
            "scale": 2.0 if NumberValue == 1 else 1.0,
            "reverse": False,
        }
        StateValue["attempts"].append(
            {
                "number": NumberValue,
                "status": "fixture_only",
                "discovery": {
                    "native_job": "unqualified-fixture",
                    "verification_job": None,
                },
                "program": Candidate,
                "candidate_sha256": RecordDigest(Candidate),
            }
        )
    Context = StateMaker(
        RunPath, KRepoRoot, JobValue, StateValue, RunPath / "Supervisor.json"
    )
    SaveContext = CastValue(Callable[[], None], getattr(Context, "Save"))
    SaveContext()
    try:
        Registration = QualifyCall(Context, StateValue["attempts"][-1])
    except StoppedError as ErrorInfo:
        print(
            EncodeJson(
                {"classification": CastValue(str, getattr(ErrorInfo, "classification"))}
            )
        )
        return 3
    print(
        EncodeJson(
            {
                "registration": Registration,
                "state": StateValue["attempts"][-1]["status"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(ProbeReserve())

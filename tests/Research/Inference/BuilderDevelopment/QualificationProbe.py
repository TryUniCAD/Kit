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

# qualification orchestration must consume real controller state from the tested checkout
KRepoRoot = FilePath(__file__).resolve().parents[4]
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))

from InferenceGrid.BuilderDevelopment.DevelopCandidate import QualifyAttempt
from InferenceGrid.BuilderDevelopment.StageState import DevelopmentStopped, StageState
from Records import digest as RecordDigest


# rejected native fixtures expose retirement behavior while never establishing acceptance
def ProbeReserve() -> int:
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
    Context = StageState(
        RunPath, KRepoRoot, JobValue, StateValue, RunPath / "Supervisor.json"
    )
    Context.Save()
    try:
        Registration = QualifyAttempt(Context, StateValue["attempts"][-1])
    except DevelopmentStopped as ErrorInfo:
        print(EncodeJson({"classification": ErrorInfo.classification}))
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

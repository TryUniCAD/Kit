# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot as KSourceRoot
from tests.Research.Inference.Authoring.Pipeline.RunPipeline import RunPipeline


# the actual controller must schedule producer and dependent decoder with one attempt each
def SubmitFixture(TmpPath: FilePath, StorePath: FilePath, FaultValue: str) -> None:
    Common = {
        "rule_version": "catalogue-pipeline-fixture@1",
        "tool_version": "fixture-only-retained-native-transport@1",
        "max_attempts": 1,
        "timeout_seconds": 90,
    }
    JobsValue = [
        {
            **Common,
            "id": "fixture-native",
            "kind": "fixture.capture.catalogue",
            "inputs": {"source": "fixture-native"},
            "options": {"fault": FaultValue},
        },
        {
            **Common,
            "id": "fixture-decode",
            "kind": "catalogue.decode",
            "depends_on": ["fixture-native"],
            "inputs": {
                "native.accepted": {"dependency": "fixture-native"},
                "bundle": {"dependency": "fixture-native", "artifact": "bundle"},
            },
            "options": {"application": "fusion"},
        },
    ]
    JobsPath = TmpPath / "Jobs.json"
    _ = JobsPath.write_text(EncodeJson({"jobs": JobsValue}), encoding="utf-8")
    _ = RunPipeline(
        KSourceRoot / "re/automation/Controller.py",
        "--store",
        StorePath,
        "submit-batch",
        JobsPath,
    )

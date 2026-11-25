# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Pipeline.RunPipeline import RunPipeline


# each decoder dependency must bind its own batch artifact rather than an aggregate capture result
def SubmitBatch(TmpPath: FilePath, StorePath: FilePath, Fault: str) -> None:
    Common = {
        "rule_version": "recipe-batch-fixture@1",
        "tool_version": "fixture-only-retained-native@1",
        "max_attempts": 1,
        "timeout_seconds": 90,
    }
    JobRows: list[dict[str, object]] = [
        {
            **Common,
            "id": "fixture-native",
            "kind": (
                "capture.catalogue.solidworks.batch"
                if Fault == "native-rejected"
                else "fixture.capture.catalogue"
            ),
            "inputs": {"source": "fixture-native"},
            "options": {"fault": Fault},
        }
    ]
    for Label in ("first", "second"):
        JobRows.append(
            {
                **Common,
                "id": "decode-" + Label,
                "kind": "catalogue.decode",
                "depends_on": ["fixture-native"],
                "inputs": {
                    "native.accepted": {"dependency": "fixture-native"},
                    "bundle": {
                        "dependency": "fixture-native",
                        "artifact": "bundle." + Label,
                    },
                },
                "options": {"application": "fusion"},
            }
        )
    JobsPath = TmpPath / "JobRows.json"
    _ = JobsPath.write_text(EncodeJson({"jobs": JobRows}), encoding="utf-8")
    _ = RunPipeline(
        KRepoRoot / "re/automation/Controller.py",
        "--store",
        StorePath,
        "submit-batch",
        JobsPath,
    )

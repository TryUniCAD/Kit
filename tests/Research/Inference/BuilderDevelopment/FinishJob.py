# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import dumps as EncodeJson, loads as DecodeJson
from collections.abc import Mapping
from pathlib import Path as FilePath
from tests.Research.Inference.Authoring.Recipes.Windows.RunController import (
    RunController,
)
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadItems import ReadItems


# rejection fixtures need real leases so resume cannot trust handwritten terminal states
def FinishJob(
    TmpPath: FilePath, Identity: str, Outcome: str, Records: Mapping[str, object]
) -> dict[str, object]:
    StorePath = TmpPath / "Run/Store"
    StemValue = HashBytes(Identity.encode()).hexdigest()[:16]
    LeasePath = TmpPath / (StemValue + "Lease.json")
    Claimed = RunController(
        StorePath, "claim", "--worker", "fixture:unlicensed", "--claim-file", LeasePath
    )
    assert Claimed.returncode == 0, Claimed.stderr
    assert DecodeJson(Claimed.stdout)["job"] == Identity
    ResultPath = TmpPath / (StemValue + "Result.json")
    _ = ResultPath.write_text(
        EncodeJson({"result": {"records": Records}}), encoding="utf-8"
    )
    Finished = RunController(
        StorePath,
        "finish",
        "--lease",
        LeasePath,
        "--result",
        ResultPath,
        "--outcome",
        Outcome,
        "--reason",
        "unlicensed process fixture",
    )
    assert Finished.returncode == 0, Finished.stderr
    Envelope = ReadRecord(DecodeJson(Finished.stdout))
    return ReadRecord(ReadItems(Envelope["jobs"])[0])

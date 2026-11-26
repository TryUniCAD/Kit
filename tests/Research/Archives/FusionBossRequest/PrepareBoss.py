# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.BossIntent.RunBossIntent import RunIntentStep
from tests.Research.Archives.FusionBossRequest.RunBossProbe import RunBossProbe
from tests.Research.Archives.FusionBossRequest.VerifyIntent import VerifyIntent


# preparation and replay must consume separate files across independent processes
def PrepareBoss(RepoPath: FilePath, WorkPath: FilePath) -> FilePath:
    SourcePath = WorkPath / "Source.json"
    LogicalPath = WorkPath / "Logical.json"
    for Arguments in (
        ("capture", "--output", str(SourcePath)),
        ("prepare", "--input", str(SourcePath), "--output", str(LogicalPath)),
    ):
        Result = RunIntentStep(WorkPath, *Arguments)
        assert Result.returncode == 0, Result.stderr
    PrepPath = WorkPath / "Prepared"
    Result = RunBossProbe(
        RepoPath,
        WorkPath,
        "--prepare",
        "--source-json",
        str(SourcePath),
        "--logical-json",
        str(LogicalPath),
        "--output",
        str(PrepPath),
    )
    assert Result.returncode == 0, Result.stderr
    SourceHash = HashBytes(SourcePath.read_bytes()).hexdigest()
    SourcePath.unlink()
    LogicalPath.unlink()
    Request = PrepPath / "P03Request.json"
    Proof = CastValue(
        dict[str, object], ReadJson((PrepPath / "P03SourceWitness.json").read_bytes())
    )
    VerifyIntent(Proof)
    assert Proof["source_json_sha256"] == SourceHash
    assert Proof["request_sha256"] == HashBytes(Request.read_bytes()).hexdigest()
    assert not SourcePath.exists() and not LogicalPath.exists()
    return PrepPath

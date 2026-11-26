# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.Archives.FusionBossRequest.ForgeBossReq import ForgeBossReq
from tests.Research.Archives.FusionBossRequest.ReplayBoss import ReplayBoss


# rejected requests and occupied destinations must remain unchanged after each process exits
def CheckRefusals(MirrorRoot: FilePath, PrepPath: FilePath, WorkPath: FilePath) -> None:
    Request = PrepPath / "P03Request.json"
    Witness = PrepPath / "P03SourceWitness.json"
    RequestBytes, WitnessBytes = Request.read_bytes(), Witness.read_bytes()
    for Variant in ("owner", "span", "reverse", "omit", "origin"):
        Tampered = WorkPath / f"Request-{Variant}.json"
        TamperedBytes = ForgeBossReq(Request, Variant)
        _ = Tampered.write_bytes(TamperedBytes)
        OutputPath = WorkPath / f"Rejected-{Variant}"
        Result = ReplayBoss(MirrorRoot, Tampered, Witness, OutputPath)
        assert Result.returncode == 1
        assert "independently prepared source witness" in Result.stderr
        assert not OutputPath.exists() and Tampered.read_bytes() == TamperedBytes
    Occupied = WorkPath / "Occupied"
    Occupied.mkdir()
    Sentinel = Occupied / "P03-baseline-a.f3d"
    _ = Sentinel.write_bytes(b"existing destination")
    Result = ReplayBoss(MirrorRoot, Request, Witness, Occupied)
    assert Result.returncode == 1 and "new private output directory" in Result.stderr
    assert list(Occupied.iterdir()) == [Sentinel]
    assert Sentinel.read_bytes() == b"existing destination"
    assert Request.read_bytes() == RequestBytes and Witness.read_bytes() == WitnessBytes

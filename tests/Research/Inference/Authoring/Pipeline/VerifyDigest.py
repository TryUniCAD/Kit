# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.Research.Inference.Authoring.Pipeline.RunPipeline import RunPipeline


# recorded evidence must match actual source bytes and a separate public reader process
def VerifyDigest(TmpPath: FilePath, SampleValue: dict[str, object]) -> None:
    NativeBytes = (TmpPath / "NativeControl.f3d").read_bytes()
    ExpectedNeutral = RunPipeline(
        FilePath(__file__).with_name("ReadNeutral.py"), TmpPath / "NativeControl.f3d"
    )
    assert DecodeJson(ExpectedNeutral)["$type"] == "CadDocument"
    assert SampleValue["source_sha256"] == HashBytes(NativeBytes).hexdigest()
    assert (
        SampleValue["neutral_sha256"]
        == HashBytes(ExpectedNeutral.encode("utf-8")).hexdigest()
    )

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from json import dumps as EncodeJson
from pathlib import Path as FilePath
from sys import argv as Arguments

from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.adapters.base.UsabilityError import UsabilityError
from tests.Research.Archives.FreeCadReplay.AssertReplay import AssertReplay
from tests.Research.Archives.FreeCadReplay.ChangeReplay import ChangeReplay


# public transactions must preserve bytes without claiming unsupported native editability
def ObserveReplay(SourcePath: FilePath, CaseName: str) -> dict[str, object]:
    Original = SourcePath.read_bytes()
    Document = ChangeReplay(
        OpenDocument(SourcePath, SourceFormat="freecad.fcstd", StrictMode=True),
        CaseName,
    )
    Output = ByteStream(b"existing destination")
    TargetPath = SourcePath.with_name("Destination.FCStd")
    HasPath = CaseName in {"overwrite", "overwrite-allowed", "strict-path"}
    if HasPath:
        _ = TargetPath.write_bytes(b"existing destination")
    try:
        Result = WriteDocument(
            Document,
            TargetPath if HasPath else Output,
            DestFormat="freecad.fcstd",
            AllowCarrier=CaseName not in {"strict", "strict-path"},
            Overwrite=CaseName in {"overwrite-allowed", "strict-path"},
            InputValues={"rebuild": CaseName == "rebuild"},
        )
    except (ValueError, FileExistsError, UsabilityError) as Problem:
        assert CaseName not in {"unchanged", "supported", "overwrite-allowed"}
        assert Output.getvalue() == b"existing destination"
        if HasPath:
            assert TargetPath.read_bytes() == b"existing destination"
        if CaseName == "overwrite":
            assert isinstance(Problem, FileExistsError)
        if CaseName in {"strict", "strict-path"}:
            assert isinstance(Problem, UsabilityError)
        assert SourcePath.read_bytes() == Original
        return {"refused": True, "reason": str(Problem), "source_unchanged": True}
    assert CaseName in {"unchanged", "supported", "overwrite-allowed"}
    AssertReplay(Result, CaseName)
    assert (TargetPath.read_bytes() if HasPath else Output.getvalue()) == Original
    assert SourcePath.read_bytes() == Original
    return {
        "refused": False,
        "can_rebuild": CaseName == "supported",
        "source_unchanged": True,
    }


if __name__ == "__main__":
    print(
        EncodeJson(ObserveReplay(FilePath(Arguments[1]), Arguments[2]), sort_keys=True)
    )

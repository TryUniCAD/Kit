# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from re import fullmatch as MatchText
from sys import argv as ArgValues
from zipfile import ZIP_STORED as KStoredZip, ZipFile as NativeBundle


# transport fixtures publish retained native bytes without claiming fresh application acceptance
def PublishFixture(SessionPath: FilePath) -> None:
    PacketValue = DecodeJson((SessionPath / "job.json").read_bytes())
    Descriptor = PacketValue["inputs"]["source"]
    if (
        not MatchText("[0-9a-f]{64}", Descriptor["sha256"])
        or Descriptor["path"] != "inputs/" + Descriptor["sha256"]
    ):
        raise ValueError("invalid fixture source binding")
    Content = (SessionPath / Descriptor["path"]).read_bytes()
    if (
        len(Content) > 64 * 1024 * 1024
        or HashBytes(Content).hexdigest() != Descriptor["sha256"]
    ):
        raise ValueError("fixture source differs from its input pin")
    FaultValue = PacketValue["job"]["options"]["fault"]
    BundlePath = SessionPath / "work/Samples.zip"
    FileName = "../Control.f3d" if FaultValue == "unsafe" else "Control.f3d"
    if FaultValue == "malformed":
        _ = BundlePath.write_bytes(b"malformed fixture bundle")
    else:
        with NativeBundle(BundlePath, "x", compression=KStoredZip) as BundleValue:
            BundleValue.writestr(
                FileName,
                (
                    Content + b"changed fixture bytes"
                    if FaultValue == "tamper"
                    else Content
                ),
            )
    BundleBytes = BundlePath.read_bytes()
    ResultValue = {
        "outcome": "completed",
        "reason": "fixture transport of a retained native archive only",
        "records": {
            "fixture_only": True,
            "native_acceptance": False,
            "application": "fusion",
            "input_sha256": Descriptor["sha256"],
            "archives": {
                FileName: {
                    "sha256": HashBytes(Content).hexdigest(),
                    "size_bytes": len(Content),
                }
            },
        },
        "artifacts": {
            "bundle": {
                "path": BundlePath.name,
                "sha256": HashBytes(BundleBytes).hexdigest(),
                "size_bytes": len(BundleBytes),
            }
        },
    }
    _ = (SessionPath / "result.json").write_text(
        EncodeJson(ResultValue, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    PublishFixture(FilePath(ArgValues[1]).resolve())

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile

from InferenceInputs import read_input, read_json_input


# decoder jobs consume only artifacts attested by their completed native dependency
def ReadNative(SessionPath, PacketValue):
    InputsValue = PacketValue["inputs"]
    Accepted = read_json_input(SessionPath, InputsValue["native.accepted"])
    if (
        Accepted.get("session_version") != 1
        or Accepted.get("result", {}).get("outcome") != "completed"
    ):
        raise ValueError("decoding requires an accepted native capture result")
    Manifest = Accepted["output_artifacts"]
    NativeFiles = {}
    for RoleValue, Descriptor in InputsValue.items():
        if RoleValue == "native.accepted":
            continue
        Binding = Descriptor["binding"]
        Artifact = Manifest[Binding["artifact"]]
        Content = read_input(SessionPath, Descriptor, 256 * 1024 * 1024)
        if Artifact != {
            "sha256": sha256(Content).hexdigest(),
            "size_bytes": len(Content),
        }:
            raise ValueError("native source differs from its accepted artifact")
        if RoleValue == "bundle":
            Expected = Accepted["result"]["records"]["archives"]
            NativeFiles.update(ReadBundle(Content, Expected))
        elif RoleValue.startswith("native."):
            if len(Content) > 64 * 1024 * 1024:
                raise ValueError("native sample exceeds the decoder input limit")
            NativeFiles[RoleValue] = Content
        else:
            raise ValueError("unexpected catalogue decoder input role")
    if not NativeFiles or len(NativeFiles) > 48:
        raise ValueError("catalogue decoding requires one to 48 native archives")
    return NativeFiles


# retained native bundles are read in memory without extracting untrusted archive paths
def ReadBundle(Content, Expected):
    Sources = {}
    with ZipFile(BytesIO(Content)) as Bundle:
        Members = Bundle.infolist()
        if len(Members) != len(Expected) or not 1 <= len(Members) <= 48:
            raise ValueError("native bundle archive roster differs")
        if sum(Member.file_size for Member in Members) > 256 * 1024 * 1024:
            raise ValueError("native bundle exceeds its aggregate input budget")
        for Member in Members:
            FileName = Member.filename
            if (
                FileName not in Expected
                or FileName in Sources
                or PurePosixPath(FileName).name != FileName
                or "\\" in FileName
                or Member.file_size > 64 * 1024 * 1024
            ):
                raise ValueError(
                    "unsafe or unexpected native archive in capture bundle"
                )
            RawValue = Bundle.read(Member)
            if Expected[FileName] != {
                "sha256": sha256(RawValue).hexdigest(),
                "size_bytes": len(RawValue),
            }:
                raise ValueError(
                    "native bundle member differs from its capture receipt"
                )
            Sources[FileName] = RawValue
    return Sources

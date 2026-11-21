# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath


# explicit fixture metadata keeps transport evidence separate from installed native application acceptance
def WritePacket(TmpPath: FilePath, PacketName: str = "Packet") -> FilePath:
    PacketValue = {
        "feature": "family:planes:offset-plane",
        "recipe": {
            "id": "plane-offset",
            "build": ["Create a plane offset from XY by offset_mm in positive Z"],
        },
        "prerequisites": {"block": {"fixture_only": True}},
        "application": "solidworks",
        "application_build": "fixture-unlicensed",
        "source_revision": "fixture-generation-protocol",
        "supported_options": {
            "basis": "XY",
            "direction": 1,
            "instances": 1,
            "units": "mm",
        },
        "api_metadata": {"fixture_only": True},
        "documentation": [],
        "examples": [],
        "diagnostics": {"fixture_case": PacketName},
    }
    PacketPath = TmpPath / (PacketName + ".json")
    _ = PacketPath.write_text(EncodeJson(PacketValue), encoding="utf-8")
    return PacketPath

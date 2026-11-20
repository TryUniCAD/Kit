# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from sys import path

path[:0] = [
    str(Path(__file__).resolve().parents[2]),
    str(Path(__file__).resolve().parents[4] / "src"),
]

from InferenceGrid.Authoring.DecodeCapture import DecodeCapture
from InferenceGrid.Authoring.ReadNative import ReadNative
from InferenceSession import read_session
from Sessions import write_private


# accepted native samples automatically continue through deterministic public decoding
def RunDecode(SessionPath):
    PacketValue, Execution = read_session(SessionPath)
    JobValue = PacketValue["job"]
    if (
        JobValue["kind"] != "catalogue.decode"
        or set(JobValue["options"]) != {"application"}
        or JobValue["options"]["application"] not in {"fusion", "solidworks"}
    ):
        raise ValueError("invalid catalogue sample decoding job")
    Sources = ReadNative(SessionPath, PacketValue)
    RecordsValue, Artifacts = [], {}
    for IndexValue, (NameValue, Content) in enumerate(sorted(Sources.items())):
        ReportValue, Neutral = DecodeCapture(
            Content, JobValue["options"]["application"], NameValue
        )
        RecordsValue.append(ReportValue)
        if Neutral is not None:
            Relative = f"Neutral{IndexValue}.json"
            RawValue = Neutral.encode("utf-8")
            (SessionPath / "work" / Relative).write_bytes(RawValue)
            Artifacts[f"neutral.{IndexValue}"] = {
                "path": Relative,
                "sha256": sha256(RawValue).hexdigest(),
                "size_bytes": len(RawValue),
            }
    write_private(
        SessionPath / "result.json",
        {
            "outcome": "completed",
            "reason": "recorded deterministic reader results for accepted native samples",
            "records": {
                "status": (
                    "read"
                    if all(Entry["status"] == "read" for Entry in RecordsValue)
                    else "decode_unresolved"
                ),
                "samples": RecordsValue,
                "execution": Execution,
                "portable_complete": False,
            },
            "artifacts": Artifacts,
        },
    )


# a fixed entry point prevents configured native commands from entering decoder execution
def MainDecode():
    ParserValue = ArgumentParser(allow_abbrev=False)
    ParserValue.add_argument("session", type=Path)
    ArgsValue = ParserValue.parse_args()
    RunDecode(ArgsValue.session.resolve())


if __name__ == "__main__":
    MainDecode()

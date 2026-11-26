# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from sys import path

path[:0] = [str(Path(__file__).resolve().parents[2])]

from CaptureTools.Catalogue.SolidWorks.RunSolid import RunSolid
from InferenceInputs import read_json_input
from InferenceSession import read_session
from InferenceGrid.Authoring.SolidSources import ReadSolidPins
from InferenceGrid.Authoring.PackNative import PackNative
from InferenceGrid.Authoring.NativeAttempt import MakeNativePath
from Records import digest, read_record
from Sessions import write_private


# source archives enter decoding only after both owned native phases verify their receipts
def RunSolidJob(SessionPath, HostPath):
    PacketValue, Execution = read_session(SessionPath)
    JobValue = PacketValue["job"]
    if JobValue["kind"] != "capture.catalogue.solidworks" or set(
        PacketValue["inputs"]
    ) != {"case"}:
        raise ValueError("invalid catalogue SOLIDWORKS capture job")
    CaseValue = read_json_input(SessionPath, PacketValue["inputs"]["case"])
    if digest(CaseValue) != JobValue["options"].get("case_sha256"):
        raise ValueError("capture case differs from its scheduled identity")
    SourcePins = ReadSolidPins(JobValue["tool_version"])
    WorkPath = SessionPath / "work"
    ReportValue = RunSolid(
        CaseValue, MakeNativePath(SessionPath, HostPath), read_record(HostPath)
    )
    BundlePath, Manifest = PackNative(WorkPath, ReportValue)
    ReportPath = WorkPath / "NativeReport.json"
    ReportPath.write_text(dumps(ReportValue, sort_keys=True), encoding="utf-8")
    Artifacts = {}
    for RoleValue, FileValue in (("bundle", BundlePath), ("report", ReportPath)):
        RawValue = FileValue.read_bytes()
        Artifacts[RoleValue] = {
            "path": FileValue.name,
            "sha256": sha256(RawValue).hexdigest(),
            "size_bytes": len(RawValue),
        }
    write_private(
        SessionPath / "result.json",
        {
            "outcome": "completed",
            "reason": "created and independently reopened configured native samples",
            "records": {
                "application": "solidworks",
                "case": CaseValue,
                "archives": Manifest,
                "native_verified": True,
                "source_pins": SourcePins,
                "execution": Execution,
            },
            "artifacts": Artifacts,
        },
    )


# the supervisor invokes one explicitly configured native owner per capture claim
def MainSolid():
    ParserValue = ArgumentParser(allow_abbrev=False)
    ParserValue.add_argument("--host", required=True, type=Path)
    ParserValue.add_argument("session", type=Path)
    ArgsValue = ParserValue.parse_args()
    RunSolidJob(ArgsValue.session.resolve(), ArgsValue.host.resolve())


if __name__ == "__main__":
    MainSolid()

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
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
from zipfile import ZIP_STORED, ZipFile

path[:0] = [str(Path(__file__).resolve().parents[2])]

from CaptureTools.Catalogue.SolidWorks.RunSolid import RunSolid
from InferenceInputs import read_json_input
from InferenceSession import read_session
from InferenceGrid.Authoring.SolidSources import CheckSolidSrc
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
    CheckSolidSrc(JobValue["tool_version"])
    WorkPath = SessionPath / "work"
    ReportValue = RunSolid(CaseValue, WorkPath / "Capture", read_record(HostPath))
    Manifest = {}
    BundlePath = WorkPath / "Samples.zip"
    with ZipFile(BundlePath, "x", compression=ZIP_STORED) as BundleFile:
        for Archive in ReportValue["archives"]:
            SourcePath = Path(Archive["path"])
            SourceRaw = SourcePath.read_bytes()
            FileName = SourcePath.name
            if FileName in Manifest or len(SourceRaw) > 64 * 1024 * 1024:
                raise ValueError("duplicate or oversized native capture archive")
            SourceHash = sha256(SourceRaw).hexdigest()
            if (
                SourceHash != Archive["sha256"]
                or len(SourceRaw) != Archive["size_bytes"]
            ):
                raise ValueError("native sample changed before controller publication")
            BundleFile.writestr(FileName, SourceRaw)
            Manifest[FileName] = {"sha256": SourceHash, "size_bytes": len(SourceRaw)}
    if not Manifest or len(Manifest) > 48:
        raise ValueError(
            "native capture archive roster exceeds the bounded decoder batch"
        )
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

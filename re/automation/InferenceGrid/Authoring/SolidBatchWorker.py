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
from sys import path, stderr

path[:0] = [str(Path(__file__).resolve().parents[2])]

from CaptureTools.Catalogue.SolidWorks.RunSolidBatch import RunSolidBatch
from CaptureTools.Catalogue.SolidWorks.SolidBatchSize import KSolidBatchCases
from CaptureTools.Catalogue.SolidWorks.SolidRecovery import SolidRecovery
from InferenceGrid.Authoring.PackNative import PackNative
from InferenceGrid.Authoring.NativeAttempt import MakeNativePath
from InferenceGrid.Authoring.SolidSources import ReadSolidPins
from InferenceInputs import read_json_input
from InferenceSession import read_session
from Records import digest, read_record
from Sessions import write_private


# startup is shared across a small batch while every case keeps independent native and decoder evidence
def RunBatchJob(SessionPath, HostPath):
    PacketValue, Execution = read_session(SessionPath)
    JobValue = PacketValue["job"]
    if (
        JobValue["kind"] != "capture.catalogue.solidworks.batch"
        or set(PacketValue["inputs"]) != {"cases"}
        or set(JobValue["options"]) != {"cases_sha256"}
    ):
        raise ValueError("invalid catalogue SOLIDWORKS batch capture job")
    CaseRecord = read_json_input(SessionPath, PacketValue["inputs"]["cases"])
    if (
        not isinstance(CaseRecord, dict)
        or set(CaseRecord) != {"schema_version", "samples"}
        or type(CaseRecord["schema_version"]) is not int
        or CaseRecord["schema_version"] != 1
        or not isinstance(CaseRecord["samples"], list)
        or not 1 <= len(CaseRecord["samples"]) <= KSolidBatchCases
        or digest(CaseRecord) != JobValue["options"]["cases_sha256"]
    ):
        raise ValueError("native batch differs from its scheduled input")
    Samples = CaseRecord["samples"]
    Identities = set()
    for Sample in Samples:
        if (
            not isinstance(Sample, dict)
            or set(Sample) != {"sample", "case"}
            or Sample["sample"] != "solidworks:" + digest(Sample["case"])[:16]
            or Sample["sample"] in Identities
        ):
            raise ValueError("native batch sample identity is invalid or repeated")
        Identities.add(Sample["sample"])
    SourcePins = ReadSolidPins(JobValue["tool_version"])
    WorkPath = SessionPath / "work"
    Reports = RunSolidBatch(
        [Sample["case"] for Sample in Samples],
        MakeNativePath(SessionPath, HostPath),
        read_record(HostPath),
        Revision=JobValue["tool_version"],
    )
    if not isinstance(Reports, list) or len(Reports) != len(Samples):
        raise ValueError("native batch lacks a result for every case")
    Bundles, Cases, Artifacts = {}, {}, {}
    for IndexValue, (Sample, Report) in enumerate(zip(Samples, Reports, strict=True)):
        if Report["case"] != Sample["case"]:
            raise ValueError("native batch report belongs to another case")
        if "native_rejection" in Report:
            Cases[Sample["sample"]] = {
                "case": Sample["case"],
                "native_verified": False,
                "native_rejection": Report["native_rejection"],
            }
            continue
        BundlePath, Manifest = PackNative(WorkPath, Report, f"Samples{IndexValue}.zip")
        RoleValue = f"bundle.{IndexValue}"
        Bundles[RoleValue] = Manifest
        Cases[Sample["sample"]] = {
            "case": Sample["case"],
            "bundle_artifact": RoleValue,
            "archives": Manifest,
            "native_verified": Report.get("verification_mode") != "document_reopen",
            "verification_mode": Report.get("verification_mode", "fresh_process"),
        }
        Content = BundlePath.read_bytes()
        Artifacts[RoleValue] = {
            "path": BundlePath.name,
            "sha256": sha256(Content).hexdigest(),
            "size_bytes": len(Content),
        }
    ReportPath = WorkPath / "NativeReport.json"
    ReportPath.write_text(dumps({"cases": Reports}, sort_keys=True), encoding="utf-8")
    Content = ReportPath.read_bytes()
    Artifacts["report"] = {
        "path": ReportPath.name,
        "sha256": sha256(Content).hexdigest(),
        "size_bytes": len(Content),
    }
    write_private(
        SessionPath / "result.json",
        {
            "outcome": "completed",
            "reason": (
                "captured and measured every native case using the recorded verification mode"
                if len(Bundles) == len(Samples)
                else "recorded native acceptance and rejection by case using the recorded verification mode"
            ),
            "records": {
                "application": "solidworks",
                "bundles": Bundles,
                "cases": Cases,
                "execution": Execution,
                "source_pins": SourcePins,
            },
            "artifacts": Artifacts,
        },
    )


# only the fixed supervisor entry may dispatch the configured native batch owner
def MainBatchJob():
    Parser = ArgumentParser(allow_abbrev=False)
    Parser.add_argument("--host", required=True, type=Path)
    Parser.add_argument("session", type=Path)
    Args = Parser.parse_args()
    try:
        RunBatchJob(Args.session.resolve(), Args.host.resolve())
    except SolidRecovery as Fault:
        print(Fault, file=stderr)
        raise SystemExit(Fault.status) from None


if __name__ == "__main__":
    MainBatchJob()

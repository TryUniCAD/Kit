# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from zipfile import ZipFile as NativeBundle

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Contracts.ReadObject import ReadObject
from tests.Research.Inference.Authoring.Contracts.ReadText import ReadText
from tests.Research.Inference.Authoring.Recipes.ChecklistGit import RunGit


# generated private fixture objects exercise transport without claiming a measured native run
def WriteEvidence(
    Publisher: FilePath, Objects: FilePath, PlanValue: dict[str, object]
) -> None:
    Evaluation = next(iter(ReadObject(PlanValue["samples"]).items()))
    Identity, SampleValue = Evaluation
    CaseValue = ReadObject(ReadObject(SampleValue)["case"])
    CaseValue = {
        KeyText: Content for KeyText, Content in CaseValue.items() if KeyText != "id"
    }
    NativeName = "example.SLDPRT"
    NativeBytes = RunProcess(
        ["git", "show", "HEAD:re/solidworks/examples/.SLDPRT/example.SLDPRT"],
        cwd=KRepoRoot,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    BundlePath = Objects.parent / "Native.zip"
    with NativeBundle(BundlePath, "w") as Archive:
        Archive.writestr(NativeName, NativeBytes)
    ArchiveData = BundlePath.read_bytes()
    BundlePin = WriteObject(Objects, ArchiveData)
    ReportData = b'{"fixture_only":true}'
    ReportPin = WriteObject(Objects, ReportData)
    Result = {
        "session_version": 1,
        "result": {
            "outcome": "completed",
            "records": {
                "application": "solidworks",
                "case": CaseValue,
                "native_verified": True,
                "source_pins": [{"fixture_only": True}],
                "execution": {"tool_version": ReadText(PlanValue["source_revision"])},
                "archives": {
                    NativeName: {
                        "sha256": HashBytes(NativeBytes).hexdigest(),
                        "size_bytes": len(NativeBytes),
                    }
                },
            },
        },
        "output_artifacts": {
            "bundle": {"sha256": BundlePin, "size_bytes": len(ArchiveData)},
            "report": {"sha256": ReportPin, "size_bytes": len(ReportData)},
        },
    }
    ReceiptPin = WriteObject(Objects, EncodeJson(Result, sort_keys=True).encode())
    Payload = EncodeJson(
        [
            ReadText(PlanValue["source_revision"]),
            ReadText(PlanValue["mode"]),
            Identity,
            CaseValue,
            BundlePin,
            ReportPin,
            ReceiptPin,
        ]
    )
    _ = RunProcess(
        [PythonExe, "-B", "-c", KWriteEntry],
        input=Payload,
        cwd=Publisher,
        text=True,
        capture_output=True,
        check=True,
        timeout=45,
    )
    _ = RunGit(Publisher, "add", "re/CatalogueChecklist")
    _ = RunGit(Publisher, "commit", "-m", "test: publish checklist receipt")


# separate artifact paths mimic copying the exported object directory to another machine
def WriteObject(Objects: FilePath, Content: bytes) -> str:
    Digest = HashBytes(Content).hexdigest()
    Target = Objects / "objects" / Digest[:2] / Digest
    Target.parent.mkdir(parents=True, exist_ok=True)
    _ = Target.write_bytes(Content)
    return Digest


# the fixture uses the same canonical filename and source identities as published run receipts
KWriteEntry = """
import json
from pathlib import Path
import sys
sys.path.insert(0, "re/automation")
from InferenceGrid.Authoring.ChecklistRecords import CaseKey, ChecklistFingerprints
from InferenceGrid.Authoring.ChecklistExport import SaveEntry
revision, mode, identity, case, bundle, report, receipt = json.load(sys.stdin)
root = Path.cwd()
capture, reader = ChecklistFingerprints(root, revision)
plan = {"mode": mode, "samples": {identity: {"case": case}}}
SaveEntry(root, {
    "version": 1,
    "case": CaseKey(plan, identity),
    "capture": {"fingerprint": capture, "revision": revision, "receipt": receipt, "bundle": bundle, "role": "bundle", "report": report},
    "decode": {"fingerprint": reader, "revision": revision, "receipt": "0" * 64, "status": "decode_unresolved",
               "files": 1, "unresolved": 1, "unsupported": 0},
})
"""

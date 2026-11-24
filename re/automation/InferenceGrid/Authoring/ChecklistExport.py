# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from Artifacts import Artifacts
from InferenceGrid.Authoring.ChecklistRecords import (
    CaseKey,
    CheckEntry,
    ChecklistFingerprints,
    EntryPath,
    KCaptureKinds,
    KChecklist,
)
from InferenceGrid.Authoring.ChecklistReuse import ReadCapture
from InferenceGrid.CatalogueRuntime import HoldCatalogue
from Ledger import Ledger
from Records import digest, read_record
from Sessions import write_private


def AcceptedResult(State, Job):
    Pin = Job["result"]
    Envelope = read_record(State.objects.path(Pin))
    if digest(Envelope) != Pin or Envelope["result"]["outcome"] != "completed":
        raise ValueError("checklist requires a verified completed controller result")
    return Envelope


def CaptureRecord(State, Submission, Plan, Identity, CapturePin):
    (JobId,) = Submission["capture"]
    Job = State.status(JobId)["jobs"][0]
    if Job["state"] != "completed" or Job["kind"] not in KCaptureKinds:
        return None
    Accepted = AcceptedResult(State, Job)
    Records = Accepted["result"]["records"]
    Proof = (
        Records.get("cases", {}).get(Identity, Records)
        if "cases" in Records
        else Records
    )
    Role = Proof.get("bundle_artifact", "bundle")
    Manifest = Accepted["output_artifacts"]
    Capture = {
        "fingerprint": CapturePin,
        "revision": Plan["source_revision"],
        "receipt": Job["result"],
        "bundle": Manifest[Role]["sha256"],
        "report": Manifest["report"]["sha256"],
        "role": Role,
    }
    ReadCapture(State.objects, Capture, Plan, Identity)
    return Capture


def DecodeRecord(State, JobId, Capture, ReaderPin, Revision):
    Job = State.status(JobId)["jobs"][0]
    if Job["state"] != "completed":
        return None
    Records = AcceptedResult(State, Job)["result"]["records"]
    Expected = {"native.accepted": Capture["receipt"], "bundle": Capture["bundle"]}
    if (
        Job["kind"] != "catalogue.decode"
        or Records["execution"]["input_sha256"] != Expected
        or Records["execution"]["tool_version"] != Revision
    ):
        raise ValueError("checklist decoder result uses different native evidence")
    Samples = Records["samples"]
    return {
        "fingerprint": ReaderPin,
        "revision": Revision,
        "receipt": Job["result"],
        "status": Records["status"],
        "files": len(Samples),
        "unresolved": sum(len(Report.get("unresolved", ())) for Report in Samples),
        "unsupported": sum(Report["status"] == "unsupported" for Report in Samples),
    }


def SaveEntry(Root, Entry):
    CheckEntry(Entry)
    Path = Root / EntryPath(Entry)
    if Path.resolve() != Path:
        raise ValueError("catalogue checklist paths cannot contain links")
    Path.parent.mkdir(parents=True, exist_ok=True)
    if Path.exists():
        if read_record(Path) != Entry:
            raise ValueError(
                "catalogue checklist entry differs from its content address"
            )
    else:
        write_private(Path, Entry)


# only accepted case evidence leaves the private run, with optional content-addressed binaries
def ExportChecklist(Root, Directory, ObjectsPath):
    if Directory.is_relative_to(Root):
        raise ValueError(
            "checklist exports require a run directory outside the checkout"
        )
    if ObjectsPath is not None and ObjectsPath.is_relative_to(Root):
        raise ValueError("keep checklist capture objects outside the checkout")
    with HoldCatalogue(Directory):
        Plan = read_record(Directory / "AuthoringPlan.json")
        Run = read_record(Directory / "AuthoringRun.json")
        if Run["plan_sha256"] != digest(Plan) or "solidworks" not in Plan["catalogues"]:
            raise ValueError("checklist export requires a prepared SOLIDWORKS plan")
        CapturePin, ReaderPin = ChecklistFingerprints(Root, Plan["source_revision"])
        Reuse = ReadRunReuse(Directory, Run)
        Submissions = read_record(Directory / "AuthoringSubmissions.json")[
            "submissions"
        ]
        Entries = []
        with Ledger(Directory / "Store") as State:
            Objects = None if ObjectsPath is None else Artifacts(ObjectsPath)
            for Submission in Submissions:
                (Identity,) = (
                    Submission["samples"]
                    if len(Submission["samples"]) == 1
                    else (None,)
                )
                if (
                    Identity is None
                    or Plan["samples"][Identity]["application"] != "solidworks"
                ):
                    continue
                Capture = (
                    Reuse[Identity]["entry"]["capture"]
                    if Identity in Reuse
                    else CaptureRecord(State, Submission, Plan, Identity, CapturePin)
                )
                if Capture is None:
                    continue
                Decode = DecodeRecord(
                    State,
                    Submission["decode"],
                    Capture,
                    ReaderPin,
                    Plan["source_revision"],
                )
                if Objects is not None:
                    Pins = [Capture[Key] for Key in ("receipt", "bundle", "report")]
                    if Decode is not None:
                        Pins.append(Decode["receipt"])
                    for Pin in Pins:
                        if Objects.put_file(State.objects.path(Pin)) != Pin:
                            raise ValueError(
                                "checklist evidence changed while exporting"
                            )
                Entry = {
                    "version": 1,
                    "case": CaseKey(Plan, Identity),
                    "capture": Capture,
                    "decode": Decode,
                }
                SaveEntry(Root, Entry)
                Entries.append(EntryPath(Entry))
    return {
        "status": "exported",
        "entries": sorted(Entries),
        "checklist": str(Root / KChecklist),
    }


def ReadRunReuse(Directory, Run):
    Pin = Run.get("checklist_sha256")
    if Pin is None:
        return {}
    Reuse = read_record(Directory / "AuthoringReuse.json")
    if digest(Reuse) != Pin:
        raise ValueError("saved catalogue reuse decisions changed")
    return Reuse

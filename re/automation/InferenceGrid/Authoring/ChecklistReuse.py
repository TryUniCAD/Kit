# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import defaultdict
from pathlib import Path

from Artifacts import Artifacts
from InferenceGrid.Authoring.ChecklistRecords import (
    CaseBody,
    CaseKey,
    ChecklistFingerprints,
    ReadEntries,
)
from InferenceGrid.Resume import BindGrid
from InferenceInputs import parse_metadata, read_file, sha256
from Ledger import Ledger
from Records import digest


# reused captures must identify the same case, bundle and measured native receipt
def ReadCapture(Store, Capture, Plan, Identity):
    Receipt = Capture["receipt"]
    Raw = read_file(Store.path(Receipt), 1024 * 1024)
    if sha256(Raw) != Receipt:
        raise ValueError("catalogue checklist capture receipt differs from its hash")
    Envelope = parse_metadata(Raw)
    Result = Envelope["result"]
    Records = Result["records"]
    Role = Capture["role"]
    Proof = (
        Records.get("cases", {}).get(Identity, Records)
        if "cases" in Records
        else Records
    )
    Manifest = Envelope["output_artifacts"]
    if (
        Envelope.get("session_version") != 1
        or Result["outcome"] != "completed"
        or Records.get("application") != "solidworks"
        or not Records.get("source_pins")
        or Records.get("execution", {}).get("tool_version") != Capture["revision"]
        or Proof.get("native_verified") is not True
        or Proof.get("case") != CaseBody(Plan, Identity)
        or Proof.get("bundle_artifact", "bundle") != Role
        or Manifest[Role]["sha256"] != Capture["bundle"]
        or Manifest["report"]["sha256"] != Capture["report"]
        or Store.verify(Capture["bundle"]) != Manifest[Role]["size_bytes"]
        or Store.verify(Capture["report"]) != Manifest["report"]["size_bytes"]
    ):
        raise ValueError(
            "catalogue checklist capture differs from accepted case evidence"
        )


def SelectReuse(Root, Plan, ObjectsPath):
    Keys = {
        CaseKey(Plan, Identity): Identity
        for Identity, Selection in Plan["samples"].items()
        if Selection["application"] == "solidworks"
    }
    if not Keys:
        return {}
    Revision = Plan["source_revision"]
    Entries = ReadEntries(Root, Revision, Keys)
    if not Entries:
        return {}
    CapturePin, ReaderPin = ChecklistFingerprints(Root, Revision)
    Choices = defaultdict(list)
    for Entry in Entries:
        if Entry["capture"]["fingerprint"] == CapturePin:
            Choices[Keys[Entry["case"]]].append(Entry)
    Store = None if ObjectsPath is None else Artifacts(ObjectsPath, create=False)
    Reuse = {}
    for Identity, Options in Choices.items():
        Exact = next(
            (
                Entry
                for Entry in Options
                if Entry["decode"] and Entry["decode"]["fingerprint"] == ReaderPin
            ),
            None,
        )
        if Exact is not None:
            Reuse[Identity] = {"mode": "result", "entry": Exact}
        elif Store is not None:
            for Entry in Options:
                Capture = Entry["capture"]
                if all(
                    Store.path(Capture[Key]).is_file()
                    for Key in ("receipt", "bundle", "report")
                ):
                    Reuse[Identity] = {"mode": "capture", "entry": Entry}
                    break
    return Reuse


# replay inputs use immutable local bindings and the same supervised decoder as fresh captures
def SubmitReuse(Directory, Plan, Reuse, ObjectsPath):
    Submissions = []
    if not any(Value["mode"] == "capture" for Value in Reuse.values()):
        return Submissions
    with Ledger(Directory / "Store") as State:
        for Identity, Value in Reuse.items():
            if Value["mode"] != "capture":
                continue
            Entry = Value["entry"]
            Capture = Entry["capture"]
            if not all(
                State.objects.path(Capture[Key]).is_file()
                for Key in ("receipt", "bundle", "report")
            ):
                Source = Artifacts(Path(ObjectsPath), create=False)
                for Key in ("receipt", "bundle", "report"):
                    Pin = Capture[Key]
                    if State.objects.put_file(Source.path(Pin)) != Pin:
                        raise ValueError(
                            "catalogue checklist artifact changed while importing"
                        )
            ReadCapture(State.objects, Capture, Plan, Identity)
            ReceiptBinding = "checklist-receipt:" + Capture["receipt"]
            BundleBinding = f"checklist-bundle:{Capture['role']}:{Capture['bundle']}"
            BindGrid(State, ReceiptBinding, Capture["receipt"])
            BindGrid(State, BundleBinding, Capture["bundle"])
            Job = "catalogue-checklist-decode:" + digest(
                [Plan["source_revision"], Entry["case"], Capture["receipt"]]
            )
            State.submit(
                {
                    "id": Job,
                    "kind": "catalogue.decode",
                    "rule_version": "catalogue-checklist@1",
                    "tool_version": Plan["source_revision"],
                    "inputs": {
                        "native.accepted": ReceiptBinding,
                        "bundle": BundleBinding,
                    },
                    "options": {"application": "solidworks"},
                }
            )
            Submissions.append({"samples": [Identity], "capture": [], "decode": Job})
    return Submissions

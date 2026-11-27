# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as ShaDigest
from pathlib import Path

from BuildReport import BuildReport
from FreezePilot import ReporterPins
from ReadRun import ReadObject, ReadRun
from Records import canonical as Canonical


# later operating events must leave a fully pinned historical report byte identical
def ReplayPilot(BundleRoot, ExpectedHash, StorePath=None):
    Snapshot, ActualHash = ReadObject(BundleRoot / "Snapshot.json")
    if ExpectedHash != ActualHash or Snapshot["version"] != 1:
        raise ValueError("snapshot SHA256 or version differs")
    if Snapshot["reporter_source_files"] != ReporterPins():
        raise ValueError("reporter source bytes differ from the frozen snapshot")
    if not isinstance(Snapshot["files"], dict) or not {
        "RunManifest.json",
        "Observation.json",
        "Events.jsonl",
        "Report.json",
    } <= set(Snapshot["files"]):
        raise ValueError("snapshot must pin every required report input")
    for FileName, ExpectedPin in Snapshot["files"].items():
        Relative = Path(FileName)
        if Relative.drive or Relative.root or ".." in Relative.parts:
            raise ValueError("snapshot member must stay within its bundle")
        FilePath = BundleRoot / Relative
        if not FilePath.resolve().is_relative_to(BundleRoot.resolve()):
            raise ValueError("snapshot member resolves outside its bundle")
        if (
            FilePath.is_symlink()
            or not FilePath.is_file()
            or ShaDigest(FilePath.read_bytes()).hexdigest() != ExpectedPin
        ):
            raise ValueError("frozen snapshot member differs")
    Manifest, _, _, _ = ReadRun(BundleRoot)
    Report = BuildReport(BundleRoot, Snapshot, StorePath or Path(Manifest["store"]))
    ReportBytes = (Canonical(Report) + "\n").encode("utf-8")
    if ReportBytes != (BundleRoot / "Report.json").read_bytes():
        raise ValueError("historical pilot report did not replay byte for byte")
    return {
        "replay": "byte_identical",
        "snapshot_sha256": ActualHash,
        "report_sha256": ShaDigest(ReportBytes).hexdigest(),
        "run_id": Report["run_id"],
        "source_revision": Report["source_revision"],
    }

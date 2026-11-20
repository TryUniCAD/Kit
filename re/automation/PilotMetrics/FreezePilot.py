# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as ShaDigest
from math import isfinite as IsFinite
from pathlib import Path
from time import time as UnixTime

from BuildReport import BuildReport
from FreezeState import FreezeState
from JournalPrefix import JournalPrefix
from PilotActivity import operating_report as OperatingReport
from PilotEvidence import SOURCES as KEvidenceSources
from ReadRun import ReadObject, ReadRun
from Records import canonical as Canonical


# content identity detects reporting code drift even when a checkout has uncommitted edits
def ReporterPins():
    SourceRoot = Path(__file__).resolve().parents[1]
    SourceFiles = sorted(SourceRoot.glob("*.py")) + sorted(
        (SourceRoot / "PilotMetrics").glob("*.py")
    )
    return {
        str(FilePath.relative_to(SourceRoot))
        .replace("\\", "/"): ShaDigest(FilePath.read_bytes())
        .hexdigest()
        for FilePath in SourceFiles
    }


# frozen bundles retain original bytes so evidence hashes survive serialization choices
def CopyFile(SourcePath, TargetPath):
    if SourcePath.is_symlink() or not SourcePath.is_file():
        raise ValueError("frozen source must be a regular nonsymlink file")
    Content = SourcePath.read_bytes()
    if len(Content) > 16 * 1024 * 1024:
        raise ValueError("frozen source exceeds 16 MiB")
    with TargetPath.open("xb") as TargetFile:
        TargetFile.write(Content)
    return ShaDigest(Content).hexdigest()


# attestation sources must be copied with their existing pins rather than reconstructed
def FreezeEvidence(ManifestPath, ExpectedHash, OutputRoot):
    Manifest, ActualHash = ReadObject(ManifestPath)
    if ExpectedHash != ActualHash:
        raise ValueError("private evidence manifest SHA256 differs")
    EvidenceRoot = OutputRoot / "Evidence"
    EvidenceRoot.mkdir()
    CopyFile(ManifestPath, EvidenceRoot / "PilotEvidence.json")
    for SourceName, ExpectedPin in Manifest["sources"].items():
        FileName = KEvidenceSources[SourceName][0]
        if (
            CopyFile(ManifestPath.parent / FileName, EvidenceRoot / FileName)
            != ExpectedPin
        ):
            raise ValueError("private evidence source SHA256 differs")
    return ActualHash


# a snapshot fixes the observed cutoff while the root owned controller continues running
def FreezePilot(
    RunRoot,
    OutputRoot,
    UntilTime=None,
    Through=None,
    EvidencePath=None,
    EvidenceHash=None,
):
    Manifest, Observe, _, _ = ReadRun(RunRoot)
    QueueState = FreezeState(Path(Manifest["store"]))
    Through = QueueState["through_event_id"] if Through is None else Through
    UntilTime = (
        min(UnixTime(), Observe["planned_until"]) if UntilTime is None else UntilTime
    )
    if (
        type(UntilTime) not in (float, int)
        or not IsFinite(UntilTime)
        or not Observe["started_at"]
        < UntilTime
        <= min(UnixTime(), Observe["planned_until"])
    ):
        raise ValueError("snapshot must end inside the actual observed pilot window")
    if (EvidencePath is None) != (EvidenceHash is None):
        raise ValueError("private manifest and SHA256 must be supplied together")
    Activity = OperatingReport(
        Path(Manifest["store"]), Observe["started_at"], UntilTime, 0, Through
    )
    PrefixBytes, _ = JournalPrefix(
        RunRoot / "Events.jsonl", Observe["started_at"], UntilTime, Manifest["run_id"]
    )
    OutputRoot.mkdir(parents=True, exist_ok=False)
    for FileName in ("RunManifest.json", "Observation.json"):
        CopyFile(RunRoot / FileName, OutputRoot / FileName)
    with (OutputRoot / "Events.jsonl").open("xb") as TargetFile:
        TargetFile.write(PrefixBytes)
    if (
        Through == QueueState["through_event_id"]
        and QueueState["observed_at"] <= UntilTime
    ):
        with (OutputRoot / "JobSnapshot.json").open("xb") as TargetFile:
            TargetFile.write((Canonical(QueueState) + "\n").encode("utf-8"))
    Snapshot = {
        "version": 1,
        "until_unix_seconds": UntilTime,
        "through_event_id": Activity["through_event_id"],
        "reporter_source_files": ReporterPins(),
    }
    if EvidencePath is not None:
        Snapshot["evidence_manifest_sha256"] = FreezeEvidence(
            EvidencePath, EvidenceHash, OutputRoot
        )
    Report = BuildReport(OutputRoot, Snapshot, Path(Manifest["store"]))
    with (OutputRoot / "Report.json").open("xb") as TargetFile:
        TargetFile.write((Canonical(Report) + "\n").encode("utf-8"))
    Snapshot["files"] = {
        str(FilePath.relative_to(OutputRoot))
        .replace("\\", "/"): ShaDigest(FilePath.read_bytes())
        .hexdigest()
        for FilePath in sorted(OutputRoot.rglob("*"))
        if FilePath.is_file()
    }
    with (OutputRoot / "Snapshot.json").open("xb") as TargetFile:
        TargetFile.write((Canonical(Snapshot) + "\n").encode("utf-8"))
    return {
        "snapshot": str(OutputRoot / "Snapshot.json"),
        "snapshot_sha256": ShaDigest(
            (OutputRoot / "Snapshot.json").read_bytes()
        ).hexdigest(),
        "report_sha256": Snapshot["files"]["Report.json"],
        "through_event_id": Activity["through_event_id"],
        "until_unix_seconds": UntilTime,
    }

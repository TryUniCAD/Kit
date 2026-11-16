from __future__ import annotations

from hashlib import sha256 as HashBytes
from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.CorpusPaths import (
    KCurveCorpus,
    KCurveLock,
    KSourceProof,
)
from tests.convert.solidworks.research.Curve.ReadObject import ReadObject


# fixture provenance must match both its lock and the actual committed metadata
def ReadManifest() -> dict[str, object]:
    Manifest = ReadObject(KCurveCorpus / "Manifest.json")
    Evidence = ReadObject(KCurveCorpus / "SourceEvidence.json")
    LockData = ReadObject(KCurveLock)
    SourceProof = ReadObject(KSourceProof)
    SourceLock = CastValue(dict[str, object], Manifest["source_lock"])
    OriginalLock = CastValue(dict[str, object], SourceProof["original_lock"])
    Provenance = CastValue(dict[str, object], LockData["publication_provenance"])
    RawSources = CastValue(dict[str, dict[str, object]], SourceProof["raw_sources"])
    LedgerHash = HashBytes(
        (KCurveCorpus / "PrivacyLedger.json").read_bytes()
    ).hexdigest()
    assert Manifest["schema"] == "kit.sw2026.curve-discovery-fixtures.v1"
    assert Manifest["version"] == 19000
    assert Manifest["is_writer_output"] is False
    assert Manifest["native_acceptance_inherited"] is False
    assert SourceLock["heldout_native_payloads_included"] == 0
    assert (
        SourceLock["sha256"]
        == OriginalLock["sha256"]
        == Provenance["original_raw_sha256"]
    )
    assert SourceLock["source_revision"] == LockData["generator_revision"]
    assert Evidence["source_lock"] == SourceLock
    assert Evidence["heldout_payloads_read"] == 0
    assert (
        SourceLock["owner_verification_sha256"]
        == RawSources["CurvesSourceLock02/RootLockVerification.json"]["sha256"]
    )
    assert (
        Evidence["manifest_sha256"]
        == HashBytes((KCurveCorpus / "Manifest.json").read_bytes()).hexdigest()
    )
    assert (
        Evidence["privacy_ledger_sha256"]
        == Manifest["privacy_ledger_sha256"]
        == LedgerHash
    )
    return Manifest

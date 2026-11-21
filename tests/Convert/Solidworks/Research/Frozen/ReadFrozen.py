from __future__ import annotations

from hashlib import sha256 as HashBytes

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# historical evidence needs an immutable source inventory independent from the current writer
def ReadFrozen() -> dict[str, object]:
    ManifestPath = KRepoRoot / "re/solidworks/v2026/heldout/FrozenCohortSource.json"
    assert (
        HashBytes(ManifestPath.read_bytes()).hexdigest()
        == "f07325a243573e6f93cb5af7d84070a2949cd849eadc96a8fcd559706bfd5d00"
    )
    Manifest = ReadObject(ManifestPath)
    assert Manifest["schema"] == "kit.sw2026.frozen-cohort-source.v1"
    assert Manifest["source_revision"] == "f5953529e2114b5648cfe1e5341a83b1c2f0d9d6"
    assert Manifest["source_file_count"] == 3404
    assert Manifest["native_acceptance_inherited"] is False
    return Manifest

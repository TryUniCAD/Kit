from __future__ import annotations

from tests.convert.solidworks.research.ArchiveProcess import KCorpus, RunArchive

KStreams = (
    "Contents/CMgr",
    "Contents/Config-0",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/Definition",
    "_MO_VERSION_19000/Biography",
    "_MO_VERSION_19000/History",
)


def TestArchive() -> None:
    Outcome = RunArchive(str(KCorpus / "*.SLDPRT"), ",".join(KStreams))
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    assert "56/56 streams round-trip with no tail across 8 files" in Outcome.stdout

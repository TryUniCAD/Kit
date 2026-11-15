from __future__ import annotations

from tests.convert.solidworks.research.ArchiveProcess import KCorpus, RunArchive


def TestLinkedArchives() -> None:
    Outcome = RunArchive(
        str(KCorpus / "*.SLDPRT"),
        "Contents/Config-0-ResolvedFeatures",
        ("--link-config",),
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    assert "8/8 streams round-trip with no tail across 8 files" in Outcome.stdout

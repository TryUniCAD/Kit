from __future__ import annotations

from tests.Convert.Solidworks.Research.ArchiveProcess import KCorpus, RunArchive


# linked stream checks prevent independent archive maps from masking reference errors
def TestLinked() -> None:
    Outcome = RunArchive(
        str(KCorpus / "*.SLDPRT"),
        "Contents/Config-0-ResolvedFeatures",
        ("--link-config",),
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    assert "8/8 streams round-trip with no tail across 8 files" in Outcome.stdout

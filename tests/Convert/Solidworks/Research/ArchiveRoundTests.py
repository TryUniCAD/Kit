from __future__ import annotations

from tests.Convert.Solidworks.Research.ArchiveProcess import KCorpus, RunArchive

# explicit critical streams prevent partial decoding from implying complete native coverage
KStreams = (
    "Contents/CMgr",
    "Contents/Config-0",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/Definition",
    "_MO_VERSION_19000/Biography",
    "_MO_VERSION_19000/History",
)


# native corpus coverage keeps recovered field grammars accountable to complete streams
def TestArchive() -> None:
    Outcome = RunArchive(str(KCorpus / "*.SLDPRT"), ",".join(KStreams))
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    assert "56/56 streams round-trip with no tail across 8 files" in Outcome.stdout

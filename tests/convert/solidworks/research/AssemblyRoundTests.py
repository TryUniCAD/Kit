from __future__ import annotations

from tests.convert.solidworks.research.ArchiveProcess import KRepoRoot, RunArchive

KCorpus = KRepoRoot / "re" / "solidworks" / "v2026" / "corpus" / "assemblies"
KStreams = (
    "Contents/CMgr",
    "Contents/Config-0",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/Definition",
    "_MO_VERSION_19000/Biography",
    "_MO_VERSION_19000/History",
)


def TestAssembly() -> None:
    Outcome = RunArchive(str(KCorpus / "*.SLDASM"), ",".join(KStreams))
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    assert "14/14 streams round-trip with no tail across 2 files" in Outcome.stdout

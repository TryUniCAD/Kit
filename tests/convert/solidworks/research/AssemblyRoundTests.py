from __future__ import annotations

from tests.convert.solidworks.research.ArchiveProcess import KRepoRoot, RunArchive

# native assembly controls anchor source document compatibility without supplying writer defaults
KCorpus = KRepoRoot / "re" / "solidworks" / "v2026" / "corpus" / "assemblies"

# assembly loader dependencies must round trip together to expose cross stream context errors
KStreams = (
    "Contents/CMgr",
    "Contents/Config-0",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/Definition",
    "_MO_VERSION_19000/Biography",
    "_MO_VERSION_19000/History",
)


# assembly source preservation requires exact object round trips across every selected critical stream
def TestAssembly() -> None:
    Outcome = RunArchive(str(KCorpus / "*.SLDASM"), ",".join(KStreams))
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    assert "14/14 streams round-trip with no tail across 2 files" in Outcome.stdout

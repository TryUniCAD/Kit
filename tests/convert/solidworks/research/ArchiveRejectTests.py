from __future__ import annotations

from tests.convert.solidworks.research.ArchiveProcess import KCorpus, RunArchive


def TestEmptyMatch() -> None:
    Outcome = RunArchive(str(KCorpus / "Missing.SLDPRT"), "Contents/Definition")
    assert Outcome.returncode == 1, Outcome.stdout + Outcome.stderr
    assert "no input files matched" in Outcome.stderr


def TestAbsent() -> None:
    Outcome = RunArchive(str(KCorpus / "L1_boss.SLDPRT"), "Contents/Missing")
    assert Outcome.returncode == 1, Outcome.stdout + Outcome.stderr
    assert "required stream is missing: Contents/Missing" in Outcome.stdout

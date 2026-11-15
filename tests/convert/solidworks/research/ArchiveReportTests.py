from __future__ import annotations

from pathlib import Path as FilePath

from tests.convert.solidworks.research.ArchiveProcess import KCorpus, RunArchive


# malformed input must produce structured diagnostics without a successful conversion claim
def TestBadArchive(TmpPath: FilePath) -> None:
    SourcePath = KCorpus / "L1_boss.SLDPRT"
    BrokenPath = TmpPath / "Truncated.SLDPRT"
    ReportPath = TmpPath / "Report.json"
    assert BrokenPath.write_bytes(SourcePath.read_bytes()[:64]) == 64
    Outcome = RunArchive(
        str(BrokenPath), "Contents/Definition", ("--report", str(ReportPath))
    )
    assert Outcome.returncode == 1, Outcome.stdout + Outcome.stderr
    ReportText = ReportPath.read_text(encoding="utf-8")
    assert '"passed": false' in ReportText
    assert '"file_count": 1' in ReportText
    assert '"stream_count": 0' in ReportText
    assert '"error":' in ReportText

from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.CliResearch.OpenLegacy import KLegacyRevision, OpenLegacy
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ReadHead, ResearchRoot


# legacy capability boundaries must stay reproducible after stacked branches are deleted
@MarkValue.parametrize("HasComparator", (False, True))
def CheckOldCompare(TmpPath: FilePath, HasComparator: bool) -> None:
    RootPath = ResearchRoot()
    Revision = ReadHead(RootPath) if HasComparator else KLegacyRevision
    with OpenLegacy(RootPath, TmpPath, Revision) as Legacy:
        Automation = Legacy / "re" / "automation"
        assert (Automation / "CompareDecoded.py").is_file() == HasComparator
        UnifiedScript = Automation / "UnifiedExports.py"
        if HasComparator:
            assert UnifiedScript.is_file()
            UnifiedScript.unlink()
        assert not UnifiedScript.exists()
        Reply = ResearchCli(TmpPath, "compare", "--help", Checkout=Legacy)
    assert Reply.returncode == 1, Reply.stderr + Reply.stdout
    assert "Research compare requires a trusted checkout" in Reply.stderr
    assert "re/automation/CompareDecoded.py" in Reply.stderr
    assert "UnifiedExports.py" in Reply.stderr

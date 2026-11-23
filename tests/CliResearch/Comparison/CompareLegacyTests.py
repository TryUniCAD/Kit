from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.CliResearch.OpenLegacy import KLegacyRevision, OpenLegacy
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot


# older source checkouts must explain both generations of missing comparison capability
@MarkValue.parametrize(
    "Revision,HasComparator",
    (
        (KLegacyRevision, False),
        ("0a137c5e02b270c00727534963288a047d723c31", True),
    ),
)
def CheckOldCompare(TmpPath: FilePath, Revision: str, HasComparator: bool) -> None:
    with OpenLegacy(ResearchRoot(), TmpPath, Revision) as Legacy:
        Automation = Legacy / "re" / "automation"
        assert (Automation / "CompareDecoded.py").is_file() == HasComparator
        assert not (Automation / "UnifiedExports.py").exists()
        Reply = ResearchCli(TmpPath, "compare", "--help", Checkout=Legacy)
    assert Reply.returncode == 1, Reply.stderr + Reply.stdout
    assert "Research compare requires a trusted checkout" in Reply.stderr
    assert "re/automation/CompareDecoded.py" in Reply.stderr
    assert "UnifiedExports.py" in Reply.stderr

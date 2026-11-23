from pathlib import Path as FilePath

from tests.CliResearch.OpenLegacy import OpenLegacy
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot


# a real older checkout must explain its missing comparison tool before attempting any work
def CheckOldCompare(TmpPath: FilePath) -> None:
    with OpenLegacy(ResearchRoot(), TmpPath) as Legacy:
        Reply = ResearchCli(TmpPath, "compare", "--help", Checkout=Legacy)
    assert Reply.returncode == 1, Reply.stderr + Reply.stdout
    assert "Research compare requires a trusted checkout" in Reply.stderr
    assert "re/automation/CompareDecoded.py" in Reply.stderr

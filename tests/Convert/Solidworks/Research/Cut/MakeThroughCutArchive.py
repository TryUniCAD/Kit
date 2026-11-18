from convert.adapters.solidworks.Core.Preparation.ThroughAll.PrepareThroughPart import (
    PrepareThroughPart,
)
from tests.Convert.Solidworks.Research.Cut.MakeThroughCutDoc import MakeThroughCutDoc


# every test part passes from authored neutral ownership to native bytes before the ordinary reader opens it
def MakeThroughCutArchive(AxisValue: str, Reverse: bool, Both: bool) -> bytes:
    Document = MakeThroughCutDoc(AxisValue, Reverse, Both)
    return PrepareThroughPart(
        Document, r"C:\KitSdkCandidates\GeneratedThroughCut.SLDPRT", 1794001000
    ).BytesValue

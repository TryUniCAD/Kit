from convert.adapters.solidworks.Core.Preparation.ThroughAll.PrepareThroughPart import (
    BuildThruPart,
)
from tests.Convert.Solidworks.Research.Cut.MakeThroughCutDoc import MakeThruCutDoc


# every test part passes from authored neutral ownership to native bytes before the ordinary reader opens it
def MakeThruArchive(AxisValue: str, Reverse: bool, BothEnds: bool) -> bytes:
    Document = MakeThruCutDoc(AxisValue, Reverse, BothEnds)
    return BuildThruPart(
        Document, r"C:\KitSdkCandidates\GeneratedThroughCut.SLDPRT", 1794001000
    ).BytesValue

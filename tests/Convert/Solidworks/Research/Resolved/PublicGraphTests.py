from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle
from tests.Convert.Solidworks.Research.Config.MakeConfigTail import MakeConfigTail
from tests.Convert.Solidworks.Research.Resolved.AssertTypedRead import AssertTypedRead
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead
from tests.Convert.Solidworks.Research.Resolved.StaleKeywords import StaleKeywords


# generated neutral inputs must expose typed dimensions and dependency aliases through the real public reader process
def TestPublicGraph(TmpPath: FilePath) -> None:
    Request = MakeMateInput("publictypedgraph")
    Bundle = CastValue(dict[str, object], Request["bundle"])
    Child = CastValue(dict[str, object], Bundle["child"])
    DocumentInput = CastValue(dict[str, object], Child["document"])
    DepthValue = 0.013875
    DocumentInput["depth_m"] = DepthValue
    _, ChildPath = RunMateBundle(Request, TmpPath / "pair")
    Document = RunPublicRead(ChildPath)
    AssertTypedRead(Document, DepthValue)
    ChangedPath = StaleKeywords(ChildPath)
    Changed = RunPublicRead(ChangedPath)
    AssertTypedRead(Changed, DepthValue)
    assert tuple(Feature.id for Feature in Changed.feature_timeline) == tuple(
        Feature.id for Feature in Document.feature_timeline
    )
    assert tuple(Sketch.id for Sketch in Changed.sketches) == tuple(
        Sketch.id for Sketch in Document.sketches
    )
    Rejected = RunPublicRead(MakeConfigTail(ChildPath))
    Evidence = CastValue(
        dict[str, object], Rejected.metadata["solidworks.typed_resolved_semantics"]
    )
    assert (
        Evidence["status"] == "unsupported" and Evidence["full_linked_graph"] is False
    )
    assert "trailing bytes" in CastValue(str, Evidence["diagnostic"])
    assert all(
        not Feature.attributes["typed_archive_owner"]
        for Feature in Rejected.feature_timeline
    )

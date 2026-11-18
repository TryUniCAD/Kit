from collections.abc import Mapping
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Resolved.AssertTypedRead import AssertTypedRead
from tests.Convert.Solidworks.Research.Resolved.Presentation.MakeTreeInput import (
    MakeTreeInput,
)
from tests.Convert.Solidworks.Research.Resolved.Presentation.RunTreeBuild import (
    RunTreeBuild,
)
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# a real authored folder permutation must keep its names and modeling semantics outside the narrow ordinary presentation profile
def TestCustomOrder(TmpPath: FilePath) -> None:
    DepthValue = 0.015625
    Request = MakeTreeInput("treefolderorder", 0.0413, 0.0269, DepthValue)
    Settings = CastValue(dict[str, object], Request["settings"])
    SystemValue = CastValue(dict[str, object], Settings["system"])
    FoldersValue = CastValue(list[tuple[str, str]], SystemValue["folders"])
    FoldersValue[0] = (FoldersValue[0][0], "User annotated comments")
    FoldersValue[0], FoldersValue[1] = FoldersValue[1], FoldersValue[0]
    ChildPath = RunTreeBuild(Request, TmpPath / "pair")
    Document = RunPublicRead(ChildPath)
    AssertTypedRead(Document, DepthValue)
    Evidence = CastValue(
        Mapping[str, object], Document.metadata["solidworks.typed_resolved_semantics"]
    )
    TreeValue = CastValue(Mapping[str, object], Evidence["native_tree"])
    assert TreeValue["status"] == "unqualified"
    assert len(Document.feature_timeline) == 19
    assert any(
        Feature.name == "User annotated comments"
        for Feature in Document.feature_timeline
    )

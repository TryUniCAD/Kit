from collections.abc import Mapping
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Resolved.AssertTypedRead import AssertTypedRead
from tests.Convert.Solidworks.Research.Resolved.Presentation.AddUnknownRow import (
    AddUnknownRow,
)
from tests.Convert.Solidworks.Research.Resolved.Presentation.MakeTreeInput import (
    MakeTreeInput,
)
from tests.Convert.Solidworks.Research.Resolved.Presentation.RunTreeBuild import (
    RunTreeBuild,
)
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# unowned rows must survive complete container and public reader boundaries even when their labels resemble runtime helpers
def TestCustomTree(TmpPath: FilePath) -> None:
    DepthValue = 0.01953125
    Request = MakeTreeInput("treeauthored", 0.0381, 0.0247, DepthValue)
    ChildPath = RunTreeBuild(Request, TmpPath / "pair")
    for KindValue, NativeId in (
        ("Notes", 9017),
        ("Sheet-Metal Master", -1),
        ("Exploded Views", 9031),
    ):
        Document = RunPublicRead(AddUnknownRow(ChildPath, KindValue, NativeId))
        AssertTypedRead(Document, DepthValue)
        Evidence = CastValue(
            Mapping[str, object],
            Document.metadata["solidworks.typed_resolved_semantics"],
        )
        TreeValue = CastValue(Mapping[str, object], Evidence["native_tree"])
        assert TreeValue["status"] == "unqualified"
        assert len(Document.feature_timeline) == 20
        (Authored,) = tuple(
            Feature
            for Feature in Document.feature_timeline
            if Feature.id == f"sldprt:feature:{NativeId}"
        )
        assert Authored.name == "authored preserved row"
        assert Authored.attributes["native_type"] == KindValue

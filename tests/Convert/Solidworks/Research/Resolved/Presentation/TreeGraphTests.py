from pathlib import Path as FilePath

from tests.Convert.Solidworks.Research.Resolved.AssertTypedRead import AssertTypedRead
from tests.Convert.Solidworks.Research.Resolved.Presentation.AssertTreeRead import (
    AssertTreeRead,
)
from tests.Convert.Solidworks.Research.Resolved.Presentation.MakeTreeInput import (
    MakeTreeInput,
)
from tests.Convert.Solidworks.Research.Resolved.Presentation.RunTreeBuild import (
    RunTreeBuild,
)
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# the real public reader must preserve live geometry and parameters while exposing separate default presentation roles
def TestDefaultTree(TmpPath: FilePath) -> None:
    for NameValue, WidthValue, HeightValue, DepthValue in (
        ("treerectalpha", 0.0317, 0.0183, 0.011125),
        ("treerectbeta", 0.0469, 0.0271, 0.019375),
    ):
        Request = MakeTreeInput(NameValue, WidthValue, HeightValue, DepthValue)
        ChildPath = RunTreeBuild(Request, TmpPath / NameValue)
        Document = RunPublicRead(ChildPath)
        AssertTypedRead(Document, DepthValue)
        AssertTreeRead(Document)

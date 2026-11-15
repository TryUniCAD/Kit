from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.Geometry.BuildStale import BuildStale
from tests.convert.Commands.WrapDocument import WrapDocument


@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckStaleBody(IsNested: bool, HasOutput: bool, TmpPath: FilePath) -> None:
    Document = BuildStale()
    assert "fusion.authoring" in Document.metadata
    Document.AssertValid()
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "UnqualifiedGeometry", HasOutput, TmpPath)

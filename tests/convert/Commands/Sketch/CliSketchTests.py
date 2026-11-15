from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.Sketch.BuildSketches import BuildSketches
from tests.convert.Commands.WrapDocument import WrapDocument


@TestMark.parametrize("RecordKind", ("Empty", "Unrelated", "Partial"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckSketchHist(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildSketches(RecordKind)
    assert Document.parameters and Document.sketches
    assert not Document.bodies and Document.brep is None
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(
        Document,
        "MissingFeatureHistory" if RecordKind == "Empty" else "IncompleteFeature",
        HasOutput,
        TmpPath,
    )

from base64 import b64decode as DecodeBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

import pytest as PytestLib

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Container.Format import (
    COMPONENT_TREE_STREAM as ComponentTreeStream,
    KEYWORDS_STREAM as KeywordsStream,
)
from tests.Convert.Solidworks.Research.Assembly.RepeatedOccurrenceBundleTests import (
    MakeRepeatInput,
)
from tests.Convert.Solidworks.Research.Assembly.RootRequest import RootRequest
from tests.Convert.Solidworks.Research.Assembly.RunRootProcess import RunRootProcess


# opt in metadata must preserve every previously measured assembly and child binary stream
def AssertXml(Baseline: dict[str, object], Indexed: dict[str, object]) -> None:
    Before = SldprtArchive.from_bytes(DecodeBytes(CastValue(str, Baseline["blob"])))
    After = SldprtArchive.from_bytes(DecodeBytes(CastValue(str, Indexed["blob"])))
    assert set(After.streams) - set(Before.streams) == {
        ComponentTreeStream,
        KeywordsStream,
    }
    assert all(
        After.require(NameValue) == BlobValue
        for NameValue, BlobValue in Before.streams.items()
    )
    BeforeChild = CastValue(dict[str, str], Baseline["child"])
    AfterChild = CastValue(dict[str, str], Indexed["child"])
    Before = SldprtArchive.from_bytes(DecodeBytes(BeforeChild["blob"]))
    After = SldprtArchive.from_bytes(DecodeBytes(AfterChild["blob"]))
    assert Before.streams.keys() == After.streams.keys()
    assert [
        NameValue
        for NameValue in Before.streams
        if Before.require(NameValue) != After.require(NameValue)
    ] == [KeywordsStream]
    XmlReport = CastValue(dict[str, object], Indexed["xml_metadata"])
    assert (
        XmlReport["native_feature_ids"]
        == XmlReport["keyword_reference_ids"]
        == [17, 18, 19]
    )
    assert Indexed["denied_reads"] == [] and Indexed["model_code_reads"]


# opening actual siblings verifies assembly placement and child history through the public boundary
def TestXmlAssembly(TmpPath: FilePath) -> None:
    Request = MakeRepeatInput("IndexedAssembly")
    Result = RunRootProcess({**Request, "include_xml_metadata": True})
    AssertXml(RunRootProcess(Request), Result)
    ParentPath = TmpPath / "IndexedAssembly.SLDASM"
    ChildPath = TmpPath / "GeneratedChildFile.SLDPRT"
    _ = ParentPath.write_bytes(DecodeBytes(CastValue(str, Result["blob"])))
    _ = ChildPath.write_bytes(
        DecodeBytes(CastValue(dict[str, str], Result["child"])["blob"])
    )
    with PytestLib.raises(
        SldprtFormatError, match="contains no readable Parasolid payload"
    ):
        _ = OpenDocument(ParentPath)
    Document = OpenDocument(ParentPath, include_brep=False, include_tessellation=False)
    Assembly = Document.assembly
    assert Document.validate() == () and Assembly is not None
    assert len(Assembly.definitions) == 2 and len(Assembly.documents) == 1
    assert len(Assembly.instances) == 3
    assert len({Instance.definition_id for Instance in Assembly.instances}) == 1
    assert [
        Instance.transform.TransformPoint((1.0, 2.0, 3.0))
        for Instance in Assembly.instances
    ] == [
        (1.0, 2.0, 3.0),
        (98.0, -4.0, 3.0),
        (16.0, 47.0, 3.0),
    ]
    ChildModel = Assembly.documents[0].document
    assert len(ChildModel.support_planes) == 3 and len(ChildModel.sketches) == 1
    assert ChildModel.sketches[0].support_plane_id == "sldprt:plane:14"
    assert (
        ChildModel.sketches[0].attributes["support_plane_source"] == "plane-reference"
    )


# an assembly without occurrences still needs both indexes for public format dispatch
def TestEmptyXml(TmpPath: FilePath) -> None:
    Request = RootRequest("IndexedEmpty", 0.25)
    Request["output"] = {
        "path_name": r"C:\Users\Public\Documents\KitOracle\IndexedEmpty.SLDASM",
        "saved_at": 1794700075,
    }
    Report = RunRootProcess({**Request, "include_xml_metadata": True})
    assert Report["denied_reads"] == []
    PathValue = TmpPath / "IndexedEmpty.SLDASM"
    _ = PathValue.write_bytes(DecodeBytes(CastValue(str, Report["blob"])))
    Document = OpenDocument(PathValue)
    assert Document.validate() == () and Document.assembly is not None
    assert len(Document.assembly.definitions) == 1
    assert not Document.assembly.instances and not Document.assembly.documents

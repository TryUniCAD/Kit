from pathlib import Path as FilePath
from xml.etree.ElementTree import tostring as XmlBytes

from pytest import mark as TestMark, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.Assembly import Elements, XmlRoot
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import (
    KComponentTreeStream,
    KConfigStream,
)
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from tests.Convert.Solidworks.NestedWriting.MakeNestDoc import MakeNestDoc


# all component reads use physically present generated member files
def WriteTestNest(TmpPath: FilePath) -> tuple[FilePath, TargetDocument]:
    Candidates = PrepNestedAsm(
        MakeNestDoc(), r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937
    )
    for NativePath, Candidate in Candidates:
        _ = (TmpPath / NativePath.name).write_bytes(Candidate.BytesValue)
    RootPath, RootValue = Candidates[-1]
    return TmpPath / RootPath.name, RootValue


# a recognized physical index conflict must refuse strict reads and remain visible during permissive inspection
@TestMark.parametrize(
    ("ChangedField", "Diagnostic"),
    (
        ("placement", "nested index placement differs from its physical owner"),
        ("file", "nested index file does not match its physical header"),
        ("config", "nested index configuration does not match its active owner"),
    ),
)
def TestNestIndex(TmpPath: FilePath, ChangedField: str, Diagnostic: str) -> None:
    Target, RootValue = WriteTestNest(TmpPath)
    assert OpenDocument(Target).assembly is not None

    Streams = dict(RootValue.StreamsValue)
    TreeValue = XmlRoot(Streams[KComponentTreeStream])
    if ChangedField == "placement":
        Reference = Elements(TreeValue, "swReference")[0]
        PoseValue = Reference.attrib["swTransform"].split()
        PoseValue[12] = str(float(PoseValue[12]) + 0.125)
        Reference.attrib["swTransform"] = " ".join(PoseValue)
    elif ChangedField == "file":
        FileRow = next(
            Value
            for Value in Elements(TreeValue, "swFile")
            if Value.attrib["swPath"].endswith(Target.name)
        )
        Stamp = FileRow.attrib["swCreationTime"]
        FileRow.attrib["swCreationTime"] = str(int(Stamp) + 1)
    else:
        (ActiveValue,) = Elements(TreeValue, "swConfiguration")
        IndexedRoot = next(
            Value
            for Value in Elements(TreeValue, "swModel")
            if Value.attrib["id"] == ActiveValue.attrib["swModelRef"]
        )
        IndexedRoot.attrib["swConfigurationName"] = "Unowned"
    Streams[KComponentTreeStream] = XmlBytes(TreeValue, encoding="utf-8")
    _ = Target.write_bytes(BuildSldprt(Streams, FormatVersion=4))

    with RaisesError(SldprtFormat, match=Diagnostic):
        _ = OpenDocument(Target)
    Partial = OpenDocument(Target, strict=False)
    assert Partial.assembly is not None
    assert any(
        Record.code == "sldasm.nested_index_conflict" and Record.message == Diagnostic
        for Record in Partial.diagnostics
    )


# the typed occurrence path and physical header can use different casing for one file
def TestNestCasing(TmpPath: FilePath) -> None:
    Target, RootValue = WriteTestNest(TmpPath)
    Before = OpenDocument(Target)
    Reference = RootValue.ReferenceValues[0]
    FileValue = RequireNode(Reference.FieldsValue["f3b0"], "moExtObject_c")
    assert any(
        Value is FileValue for Value in HeaderRefNodes(RootValue.HeaderValue, 19000)
    )
    Fields = RequireRecord(FileValue.FieldsValue["shared"])
    Handle = RequireNode(Fields["h18"], "moCStringHandle_c")
    Locator = Handle.FieldsValue["value"]
    assert isinstance(Locator, CStringValue)
    Folded = Locator.TextValue.lower()
    assert Locator.TextValue != Folded
    Handle.FieldsValue["value"] = CStringValue(Folded, Locator.IsUnicode)
    StreamName = KConfigStream + "-ModelHeader"
    HeaderBytes = WriteHeadGraph(RootValue.HeaderValue, 19000)
    assert HeaderBytes != RootValue.StreamsValue[StreamName]
    Streams = dict(RootValue.StreamsValue) | {StreamName: HeaderBytes}
    _ = Target.write_bytes(BuildSldprt(Streams, FormatVersion=4))
    After = OpenDocument(Target)
    assert Before.assembly is not None and After.assembly is not None
    assert After.assembly.instances == Before.assembly.instances
    assert all(
        "typed_placement_m" in Value.attributes for Value in After.assembly.instances
    )

from pathlib import Path as FilePath
from xml.etree.ElementTree import tostring as XmlBytes

from pytest import mark as TestMark, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Assembly.Assembly import Elements, XmlRoot
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KComponentTreeStream
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from tests.Convert.Solidworks.NestedWriting.MakeNestDoc import MakeNestDoc


# a recognized physical index conflict must refuse strict reads and remain visible during permissive inspection
@TestMark.parametrize(
    ("ChangePose", "Diagnostic"),
    (
        (True, "nested index placement differs from its physical owner"),
        (False, "nested index file does not match its physical header"),
    ),
)
def TestNestIndex(TmpPath: FilePath, ChangePose: bool, Diagnostic: str) -> None:
    Candidates = PrepNestedAsm(
        MakeNestDoc(), r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937
    )
    for NativePath, Candidate in Candidates[:-1]:
        _ = (TmpPath / NativePath.name).write_bytes(Candidate.BytesValue)
    RootPath, RootValue = Candidates[-1]
    Target = TmpPath / RootPath.name
    _ = Target.write_bytes(RootValue.BytesValue)
    assert OpenDocument(Target).assembly is not None

    Streams = dict(RootValue.StreamsValue)
    TreeValue = XmlRoot(Streams[KComponentTreeStream])
    if ChangePose:
        Reference = Elements(TreeValue, "swReference")[0]
        PoseValue = Reference.attrib["swTransform"].split()
        PoseValue[12] = str(float(PoseValue[12]) + 0.125)
        Reference.attrib["swTransform"] = " ".join(PoseValue)
    else:
        FileRow = next(
            Value
            for Value in Elements(TreeValue, "swFile")
            if Value.attrib["swPath"].endswith(RootPath.name)
        )
        Stamp = FileRow.attrib["swCreationTime"]
        FileRow.attrib["swCreationTime"] = str(int(Stamp) + 1)
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

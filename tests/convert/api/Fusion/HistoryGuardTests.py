from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from tests.convert.api.Fusion.AdapterCases import AdapterCase


@MarkTests.parametrize("RoleName", ("operation", "secondary", "body"))
def TestHistoryGate(TmpPath: FilePath, RoleName: str) -> None:
    Source = TmpPath / "Source.f3d"
    _ = WriteDocument(AdapterCase("extrusion"), Source, destination_format="f3d")
    Document = OpenDocument(Source)
    ModelValue = ReadDocument(Source.read_bytes())
    BodyValue = ModelValue.Bodies[0]
    Identity = BodyValue.History.Identity
    Identity = AlterIdentity(Identity, RoleName)
    History = ReplaceData(BodyValue.History, Identity=Identity)
    Changed = ReplaceData(ModelValue, Bodies=(ReplaceData(BodyValue, History=History),))
    Corrupt = TmpPath / "Corrupt.f3d"
    _ = Corrupt.write_bytes(EmitParsed(Changed))
    with RaisesError(ValueError, match="qualified authored feature profile"):
        _ = OpenDocument(Corrupt)
    Contract = {"version": 1, "model": EncodeState(Changed)}
    Altered = ReplaceData(Document, metadata={"fusion.native_state": Contract})
    Target = TmpPath / "Rejected.f3d"
    with RaisesError(ValueError, match="qualified authored feature profile"):
        _ = WriteDocument(Altered, Target, destination_format="f3d")
    assert not Target.exists()


def AlterIdentity(Identity: BodyIdentity, RoleName: str) -> BodyIdentity:
    if RoleName == "operation":
        return ReplaceData(Identity, OperationId=302)
    if RoleName == "secondary":
        return ReplaceData(Identity, SecondaryId=15)
    return ReplaceData(Identity, BodyKey=15)

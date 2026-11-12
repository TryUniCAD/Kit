from io import BytesIO as ByteStream
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from tests.convert.formats.FusionCodec.Documents.Form.EditedWorlds import (
    KEditedWorlds,
)
from tests.convert.formats.FusionCodec.Documents.Form.FormArchives import (
    KFormArchives,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
@MarkTests.parametrize(
    "CaseValue", KFormArchives, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestFormDocs(TmpPath: FilePath, CaseValue: tuple[str, str]) -> None:
    Payload = ReadFormFile(*CaseValue)
    Model = ReadDocument(Payload)
    assert len(Model.Forms) == 1
    assert Model.Forms[0].Name.startswith("TSplines.BlobParts/TSpline.")
    Target = TmpPath / "Form.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    assert ReadDocument(Target.read_bytes()) == Model
    with ZipFile(ByteStream(Payload)) as Before, ZipFile(Target) as After:
        assert sorted(Before.namelist()) == sorted(After.namelist())
        for NameValue in Before.namelist():
            if NameValue.endswith(".tsm"):
                assert After.read(NameValue) == EmitTspline(Model.Forms[0].Surface)
            if not NameValue.endswith(".protein"):
                assert After.read(NameValue) == Before.read(NameValue)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
@MarkTests.parametrize(
    "CaseValue", KEditedWorlds, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestFormWorlds(CaseValue: tuple[str, str]) -> None:
    with RaisesError(ValueError, match="custom graphics world"):
        _ = ReadDocument(ReadFormFile(*CaseValue))

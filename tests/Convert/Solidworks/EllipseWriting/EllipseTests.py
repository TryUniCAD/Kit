from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from io import BytesIO
from typing import cast as CastValue
from zlib import ZLIB_RUNTIME_VERSION as DeflateRuntime

from pytest import mark as TestMark, raises as RaisesError

from convert.api import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import (
    PrepareEllipse,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.EllipseWriting.MakeEllipseDoc import (
    MakeEllipseDoc,
    ReadEllipseCase,
)


# canonical cold readback must preserve the actual sketch live dimension and body associations
def AssertEllipRead(Payload: bytes, DepthValue: float) -> CadDocument:
    Model = OpenDocument(Payload, source_format=KPartFormatId)
    (Sketch,) = Model.sketches
    (Entity,) = Sketch.entities
    (Parameter,) = Model.parameters
    (BodyValue,) = Model.bodies
    assert not Model.validate() and not Model.diagnostics
    assert Entity.kind == GeometryKind.KEllipse
    assert Sketch.closed_profile_entity_ids == ((Entity.id,),)
    assert Parameter.name == "D1" and Parameter.role == ParameterRole.KDriving
    assert Parameter.value.value == DepthValue
    assert Parameter.owner_id == BodyValue.final_feature_id
    assert Model.brep is not None and len(Model.brep.faces) == 3
    assert not Model.brep.validate(frozenset((BodyValue.id,)))
    return Model


# both writer entry points must preserve the caller sink when its complete payload has no matching measurement
def AssertEllipOut(
    Document: CadDocument, Options: Mapping[str, object], Payload: bytes, Measured: bool
) -> None:
    Direct, Standard = BytesIO(), BytesIO()
    if not Measured:
        with RaisesError(ValueError, match="no unique exact native measurement"):
            _ = SldprtWriter().write(Document, Direct, WriteOptions(values=Options))
        with RaisesError(ValueError, match="no unique exact native measurement"):
            _ = WriteDocument(
                Document,
                Standard,
                destination_format=KPartFormatId,
                allow_carrier=False,
                values=Options,
            )
        assert (
            Direct.tell(),
            Standard.tell(),
            Direct.getvalue(),
            Standard.getvalue(),
        ) == (0, 0, b"", b"")
        return
    Result = SldprtWriter().write(Document, Direct, WriteOptions(values=Options))
    assert Result.application_usable and Result.vendor_loadable
    Result = WriteDocument(
        Document,
        Standard,
        destination_format=KPartFormatId,
        allow_carrier=False,
        values=Options,
    )
    assert Result.application_usable and Result.vendor_loadable
    assert Direct.getvalue() == Standard.getvalue() == Payload


# the measured archive and linked readback remain guarded on every hosted compression runtime
@TestMark.parametrize("SlotValue", (0, 1))
def TestEllipCase(SlotValue: int) -> None:
    Receipt, CaseValue, StreamHashes = ReadEllipseCase(SlotValue)
    Document = MakeEllipseDoc(SlotValue)
    Clock = CastValue(int, CaseValue["written_at"])
    Settings = {
        "final_destination": CaseValue["locator"],
        "require_native_transfers": True,
        KPartMeasureOpt: {"written_at": Clock, "receipt": Receipt},
    }
    BuildValue = PrepareEllipse(
        Document, BytesIO(), Clock, WriteOptions(values=Settings)
    )
    Payload = BuildValue.BytesValue
    assert {
        NameValue: CalcSha(Value).hexdigest()
        for NameValue, Value in BuildValue.StreamsValue.items()
    } == StreamHashes
    Measured = CalcSha(Payload).hexdigest() == CaseValue["archive_sha256"]
    if "zlib-ng" not in DeflateRuntime:
        assert Measured
    AssertEllipOut(Document, Settings, Payload, Measured)
    Reopened = AssertEllipRead(
        Payload, CastValue(float, Document.parameters[0].value.value)
    )
    AssertEllipOut(
        CadDocument.from_json(Reopened.to_json()), Settings, Payload, Measured
    )
    Design = OpenDocument(Payload, source_format=KPartFormatId, include_brep=False)
    assert Design.brep is None and Design.feature_timeline == Reopened.feature_timeline
    AssertEllipOut(CadDocument.from_json(Design.to_json()), Settings, Payload, Measured)


# translated sketch stations must remain orthogonal within their binary64 construction error
def TestOffsetEllip() -> None:
    Document = MakeEllipseDoc(2)
    _, CaseValue, _ = ReadEllipseCase(0)
    Clock = CastValue(int, CaseValue["written_at"])
    Settings = WriteOptions(
        values={"final_destination": r"C:\KitSdkCandidates\EllipseTranslated.SLDPRT"}
    )
    Candidate = PrepareEllipse(Document, BytesIO(), Clock, Settings)
    _ = AssertEllipRead(Candidate.BytesValue, 15.0)
    Target = BytesIO()
    with RaisesError(ValueError, match="offline native measurement"):
        _ = SldprtWriter().write(Document, Target, Settings)
    assert Target.tell() == 0 and Target.getvalue() == b""

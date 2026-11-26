from dataclasses import replace as ReplaceValue
from hashlib import sha256 as CalcSha
from io import BytesIO
from typing import cast as CastValue

from pytest import mark as TestMark, raises as RaisesError

from convert.api import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc
from tests.Convert.Solidworks.PlainWriting.MeasuredStreamTests import SendMeasured


# measured readback uses the explicit final locator because the reader retains a physical source label
def WriteCold(
    Document: CadDocument,
    Target: BytesIO,
    Options: dict[str, object],
    IsDirect: bool,
) -> WriteResult:
    if IsDirect:
        return SldprtWriter().write(Document, Target, WriteOptions(values=Options))
    return WriteDocument(
        Document,
        Target,
        destination_format=KPartFormatId,
        allow_carrier=False,
        values=Options,
    )


# each representative neutral model must pass through the real reader before either writer opens its sink
def ReadbackCase(RoleName: str) -> tuple[CadDocument, dict[str, object], bytes]:
    Document, Envelope, Digest = MeasurePlainDoc(RoleName)
    Source = BytesIO()
    _ = SendMeasured(Document, Source, Envelope, False)
    RawValue = Source.getvalue()
    assert CalcSha(RawValue).hexdigest() == Digest
    NameValue = CastValue(str, Document.metadata["name"])
    return (
        OpenDocument(RawValue, strict=True),
        {
            "final_destination": rf"C:\KitSdkCandidates\{NameValue}.SLDPRT",
            KPartMeasureOpt: Envelope,
            "require_native_transfers": True,
        },
        RawValue,
    )


# cold strict geometry provenance and driving ownership must survive the exact generated archive
@TestMark.parametrize("RoleName", ("Skew", "Step"))
def TestColdRound(RoleName: str) -> None:
    Document, Options, RawValue = ReadbackCase(RoleName)
    (Driver,) = Document.parameters
    assert (
        Driver.name == "D1" and Driver.owner_id == Document.bodies[0].final_feature_id
    )
    (AxisSelection,) = Document.selections
    (AxisPath,) = AxisSelection.path
    assert AxisPath.subelement == "N_Axis"
    assert AxisPath.entity_id == Document.sketches[0].name
    assert Document.brep is not None and Document.sketches[0].closed_profile_entity_ids
    for IsDirect in (False, True):
        Target = BytesIO()
        Outcome = WriteCold(Document, Target, Options, IsDirect)
        assert Outcome.vendor_loadable and Outcome.application_usable
        assert (
            not Outcome.dropped and Outcome.native_capabilities == Document.capabilities
        )
        assert Capability.SELECTIONS in Outcome.native_capabilities
        assert Target.getvalue() == RawValue
        assert OpenDocument(Target.getvalue(), strict=True) == Document


# the provenance preflight must refuse changed reader fields before touching either caller sink
def TestColdScope() -> None:
    Document, Options, _ = ReadbackCase("Skew")
    (BodyValue,) = Document.bodies
    ChangedBody = ReplaceValue(
        BodyValue, topology=ReplaceValue(BodyValue.topology, face_count=17)
    )
    for Changed in (
        ReplaceValue(Document, metadata={**Document.metadata, "extra": True}),
        ReplaceValue(Document, bodies=(ChangedBody,)),
        ReplaceValue(Document, source=ReplaceValue(Document.source, sha256="0" * 64)),
    ):
        for IsDirect in (False, True):
            Target = BytesIO(b"previous")
            with RaisesError(ValueError, match="differs from its regenerated part"):
                _ = WriteCold(Changed, Target, Options, IsDirect)
            assert Target.getvalue() == b"previous" and Target.tell() == 0
    with RaisesError(ValueError, match="native-only feature definitions"):
        _ = WriteDocument(Document, BytesIO(), destination_format="interchange.json")

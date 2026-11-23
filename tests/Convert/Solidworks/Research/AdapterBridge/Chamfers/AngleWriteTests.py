from io import BytesIO

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import (
    PrepChmfPart,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import ChamferFeature
from tests.Convert.Solidworks.Research.AdapterBridge.Chamfers.AngleTestModel import (
    MakeAngleDoc,
)


# the real prepared archive keeps both editable drivers under the strict public reader
def TestAngleGate() -> None:
    Document = MakeAngleDoc()
    Locator = r"C:\KitSdkCandidates\AngleArchive.SLDPRT"
    WrittenAt = 1795510277
    Candidate = PrepChmfPart(
        Document,
        BytesIO(),
        WrittenAt,
        WriteOptions(values={"final_destination": Locator}),
    )
    Readback = OpenDocument(BytesIO(Candidate.BytesValue), source_format=KPartFormatId)
    FeatureValue = Readback.feature_timeline[-1]
    assert isinstance(FeatureValue.definition, ChamferFeature)
    assert FeatureValue.definition.mode == "distance_angle"
    LengthValue, AngleValue = (
        Value for Value in Readback.parameters if Value.id in FeatureValue.parameter_ids
    )
    assert (LengthValue.name, LengthValue.value.value) == ("D1", 3.375)
    assert (AngleValue.name, AngleValue.value.value) == ("D2", 0.625)
    assert Readback.brep is not None and len(Readback.brep.faces) == 7
    RefuseAngleMeas(Document, Locator, WrittenAt)


# trust only the authenticated measurement and preserve an occupied destination on refusal
def RefuseAngleMeas(Document: CadDocument, Locator: str, WrittenAt: int) -> None:
    TargetValue = BytesIO(b"existing content")
    try:
        _ = WriteDocument(
            Document,
            TargetValue,
            destination_format=KPartFormatId,
            allow_carrier=False,
            values={
                "final_destination": Locator,
                "solidworks_native_measurement": {
                    "written_at": WrittenAt,
                    "receipt": {"trial": {}, "native_result": {}},
                },
            },
        )
    except ValueError as ErrorValue:
        assert "requires authenticated offline evidence" in str(ErrorValue)
    else:
        raise AssertionError("unmeasured angle chamfer escaped publication")
    assert TargetValue.getvalue() == b"existing content" and TargetValue.tell() == 0

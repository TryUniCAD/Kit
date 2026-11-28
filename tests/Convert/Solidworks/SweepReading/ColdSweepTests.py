from io import BytesIO
from math import pi as PiValue

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import (
    BuildSweepPart,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Features.SweepFeature import SweepFeature
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# an authored sweep exercises cold archive recognition through the public reader
def TestColdSweep() -> None:
    Intent = SweepIntent(
        "ColdSweep",
        CircleGeometry(PlaneVector(0.0, 0.0), 0.003125),
        ArcGeometry(PlaneVector(0.0, 0.0375), 0.0375, -PiValue / 2.0, 0.0),
        997.25,
        SelfFileInput(r"C:\KitSdkCandidates\ColdSweep.SLDPRT", 1794000000),
    )
    Payload = BuildSweepPart(Intent).BytesValue
    FullValue = OpenDocument(BytesIO(Payload), source_format=KPartFormatId)
    Design = OpenDocument(
        BytesIO(Payload), source_format=KPartFormatId, include_brep=False
    )
    assert FullValue.source.attributes["cold_sweep_model"] is True
    assert "saved_sweep_result" not in FullValue.source.attributes
    assert FullValue.parameters == Design.parameters
    assert FullValue.feature_timeline == Design.feature_timeline
    assert FullValue.bodies == Design.bodies
    assert Design.brep is None and Capability.KBrep not in Design.capabilities
    (FeatureValue,) = FullValue.feature_timeline
    (BodyValue,) = FullValue.bodies
    assert isinstance(FeatureValue.definition, SweepFeature)
    assert FeatureValue.OutputBodyIds == (BodyValue.id,)
    assert tuple(Value.value.value for Value in FullValue.parameters) == (
        6.25,
        37.5,
        997.25,
    )
    assert FullValue.parameters[-1].owner_id == BodyValue.id
    assert FullValue.brep is not None and not FullValue.brep.validate(
        frozenset((BodyValue.id,))
    )
    assert len(FullValue.brep.faces) == 3 and len(FullValue.brep.pcurves) == 4
    AssertColdJson(FullValue, Intent.OutputValue.PathName)


# neutral json keeps editable history without authorizing an unmeasured native output
def AssertColdJson(Document: CadDocument, Locator: str) -> None:
    Portable = BytesIO()
    _ = WriteDocument(
        Document, Portable, destination_format="interchange.json", allow_carrier=False
    )
    Current = OpenDocument(
        BytesIO(Portable.getvalue()), source_format="interchange.json"
    )
    assert Current.to_json(indent=None) == Document.to_json(indent=None)
    Target = BytesIO()
    try:
        _ = WriteDocument(
            Current,
            Target,
            destination_format=KPartFormatId,
            allow_carrier=False,
            values={"final_destination": Locator},
        )
    except ValueError as ErrorValue:
        assert "requires an offline native measurement" in str(ErrorValue)
    else:
        raise AssertionError("cold sweep escaped the required measurement")
    assert not Target.getvalue()

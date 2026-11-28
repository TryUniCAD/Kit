from math import isclose as IsClose
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from tests.Convert.Integration.Fusion.Offsets.CheckOffsetGeom import CheckOffsetGeom
from tests.Convert.Integration.Fusion.Offsets.OffsetCase import OffsetCase


# full source reads must preserve owned controls and measured geometry together
def CheckOffsetRead(Document: CadDocument, Sample: OffsetCase) -> None:
    Reading = Sample.Reading
    assert Reading["settings_pass"] and Reading["geometry_pass"]
    assert len(Document.bodies) == 1 and len(Document.feature_timeline) == 2
    Feature = Document.feature_timeline[-1]
    Definition = Feature.definition
    assert isinstance(Definition, DistanceExtrude)
    assert Definition.SideMode == "two_sided"
    assert Definition.Direction.x == Definition.Direction.y == 0.0
    assert Definition.Direction.z == 1.0
    Parameters = {Value.id: Value for Value in Document.parameters}
    assert len(Parameters) == 5 and set(Feature.parameter_ids) == set(Parameters)
    Expected = (
        (Definition.AlongParameterId, "AlongDistance", "first", 10.0),
        (Definition.AgainstParameterId, "AgainstDistance", "second", 10.0),
        (Definition.StartOffsetId, "ProfileOffset", "offset", 10.0),
        (Definition.TaperParameterId, "TaperAngle", "draft_first", 1.0),
        (Definition.SecondTaperId, "Side2TaperAngle", "draft_second", 1.0),
    )
    assert len({Value[0] for Value in Expected}) == 5
    for Identity, NativeName, MeasureName, Factor in Expected:
        assert Identity is not None
        Parameter = Parameters[Identity]
        assert Parameter.owner_id == Feature.id
        assert Parameter.attributes["native_name"] == NativeName
        assert isinstance(Parameter.value.value, (int, float))
        assert IsClose(
            Parameter.value.value,
            CastValue(float, Reading[MeasureName]) * Factor,
            abs_tol=1e-9,
        )
    Values = GetDistValues(Feature, Definition, Parameters)
    assert IsClose(
        Values.LowerMm,
        (CastValue(float, Reading["offset"]) - CastValue(float, Reading["second"]))
        * 10,
        abs_tol=1e-9,
    )
    assert IsClose(
        Values.UpperMm,
        (CastValue(float, Reading["offset"]) + CastValue(float, Reading["first"])) * 10,
        abs_tol=1e-9,
    )
    CheckOffsetGeom(Document, Sample)
    assert Document.metadata == {"fusion.read_only": True}
    Document.AssertValid()

from math import isclose as IsClose
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# strict source projection must retain all four actual drivers and the complete solved solid
def CheckAdmitDoc(Document: CadDocument, Sample: DualCase) -> None:
    assert Document.metadata["fusion.read_only"] is True
    assert Document.brep is not None and len(Document.bodies) == 1
    Feature = Document.feature_timeline[-1]
    assert isinstance(Feature.definition, DistanceExtrude)
    Definition = Feature.definition
    Roles = (
        Definition.AlongParameterId,
        Definition.AgainstParameterId,
        Definition.TaperParameterId,
        Definition.SecondTaperId,
    )
    assert len(set(Roles)) == 4 and None not in Roles
    Parameters = {Value.id: Value for Value in Document.parameters}
    assert all(
        Parameters[CastValue(str, Identity)].owner_id == Feature.id
        for Identity in Roles
    )
    Values = GetDistValues(Feature, Definition, Parameters)
    assert IsClose(Values.LowerMm, -Sample.SecondMm, abs_tol=1e-10)
    assert IsClose(Values.UpperMm, Sample.FirstMm, abs_tol=1e-10)
    assert IsClose(Values.TaperRadians, Sample.FirstTaper, abs_tol=1e-10)
    assert Values.SecondTaperRadians is not None
    assert IsClose(Values.SecondTaperRadians, Sample.SecondTaper, abs_tol=1e-10)
    BodyValue = Document.bodies[0]
    assert (
        BodyValue.final_feature_id == Feature.id
        and BodyValue.material_id == Document.materials[0].id
    )
    assert BodyValue.topology.solid_count == 1 and BodyValue.topology.valid is True
    assert (
        BodyValue.topology.volume is not None
        and BodyValue.topology.surface_area is not None
    )
    assert IsClose(
        BodyValue.topology.volume,
        CastValue(float, Sample.Reading["volume_cm3"]) * 1000,
        rel_tol=1e-8,
    )
    assert IsClose(
        BodyValue.topology.surface_area,
        CastValue(float, Sample.Reading["area_cm2"]) * 100,
        rel_tol=1e-8,
    )
    Document.AssertValid()
    assert CadDocument.from_json(Document.to_json()) == Document

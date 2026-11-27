from dataclasses import replace as ReplaceValue

from pytest import mark as MarkTests

from convert.api.ApiOpen import OpenDocument
from convert.Geometry.Fillet.Circular.BuildRimFillet import BuildRimFillet
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.Fillets.GetFilletVals import GetFilletVals
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.RimPolicyCase import (
    RimPolicyCase,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.CheckRimMeasure import (
    CheckRimMeasure,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.ReadRimApi import ReadRimApi


# actual native radius edit observations must match a changed bound neutral model without copied radius values
@MarkTests.parametrize("Sample", ReadPolicyCases())
def CheckRimEdit(Sample: RimPolicyCase) -> None:
    Original = OpenDocument(Sample.Source)
    Document = CadDocument.from_json(Original.to_json())
    Extrude, Fillet = Document.feature_timeline[1:]
    assert isinstance(Extrude.definition, DistanceExtrude)
    assert isinstance(Fillet.definition, RadiusFillet)
    Driver = next(
        Value
        for Value in Document.parameters
        if Value.id == Fillet.definition.RadiusParameterId
    )
    EditedApi = ReadRimApi(Sample.CaseName, "edited")
    EditedRadius = dict(EditedApi.Parameters)[Driver.name] * 10
    assert EditedRadius != Driver.value.value
    Changed = ReplaceValue(Driver, value=ReplaceValue(Driver.value, value=EditedRadius))
    Document = ReplaceValue(
        Document,
        parameters=tuple(
            Changed if Value.id == Driver.id else Value for Value in Document.parameters
        ),
    )
    Document.AssertValid()
    Parameters = {Value.id: Value for Value in Document.parameters}
    Radius, Weight = GetFilletVals(
        Fillet,
        Fillet.definition,
        Parameters,
        {Value.id: Value for Value in Document.selections},
    )
    assert Radius == EditedRadius and Weight == 1
    Length = GetDistValues(Extrude, Extrude.definition, Parameters).UpperMm
    (Profile,) = (
        Value.geometry
        for Value in Document.sketches[0].entities
        if isinstance(Value.geometry, CircleGeometry)
    )
    (BodyValue,) = Document.bodies
    Geometry, Volume, AreaValue, Center, Bounds = BuildRimFillet(
        BodyValue.id, Profile.radius, Length, Radius
    )
    BodyValue = ReplaceValue(
        BodyValue,
        topology=ReplaceValue(
            BodyValue.topology,
            volume=Volume,
            surface_area=AreaValue,
            bounding_box=Bounds,
        ),
        attributes={
            **BodyValue.attributes,
            "analytic_centroid_mm": (Center.x, Center.y, Center.z),
        },
    )
    Document = ReplaceValue(Document, brep=Geometry, bodies=(BodyValue,))
    Document.AssertValid()
    CheckRimMeasure(Document, EditedApi)
    Restored = CadDocument.from_json(Original.to_json())
    assert Restored == Original and Restored.selections == Document.selections
    CheckRimMeasure(Restored, ReadRimApi(Sample.CaseName, "restored"))

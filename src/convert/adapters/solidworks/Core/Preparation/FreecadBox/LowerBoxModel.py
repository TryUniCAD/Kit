from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeBoxProfile import (
    MakeBoxProfile,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter, ParameterValue


# lowering an admitted primitive must preserve part configuration and driver identities while deriving all sketch geometry from authored lengths
def LowerBoxModel(
    DocumentValue: CadDocument,
    NameValue: str,
    ParameterIds: tuple[str, str, str],
    Dimensions: tuple[float, float, float],
    DriverNames: tuple[str, str, str],
    BodyName: str,
) -> CadDocument:
    SourceFeature = DocumentValue.feature_timeline[0]
    SourcePlane = next(
        PlaneValue
        for PlaneValue in DocumentValue.support_planes
        if PlaneValue.name == "XY-plane"
    )
    Plane = SupportPlane(SourcePlane.id, "Front Plane", SourcePlane.transform)
    LengthId, WidthId, HeightId = ParameterIds
    Length, Width, Height = Dimensions
    SketchValue = MakeBoxProfile(
        SourceFeature.id + ":profile",
        SourceFeature.name + " Profile",
        Plane.id,
        Length,
        Width,
        (LengthId, WidthId),
    )
    LengthName, WidthName, HeightName = DriverNames
    HeightValue = ParameterValue(Height, ValueKind.KLength, "mm")
    FeatureValue = FeatureStep(
        SourceFeature.id,
        SourceFeature.name,
        FeatureKind.KExtrusion,
        0,
        sketch_id=SketchValue.id,
        parameter_ids=(HeightId,),
        operation=BooleanOp.KCreate,
        definition=ExtrudeFeature(length=HeightValue),
    )
    PartValue = CadDocument(
        DocumentValue.source,
        DocumentValue.configurations,
        (
            Parameter(
                WidthId,
                WidthName,
                ParameterValue(Width, ValueKind.KLength, "mm"),
                owner_id=SketchValue.id,
            ),
            Parameter(HeightId, HeightName, HeightValue, owner_id=FeatureValue.id),
            Parameter(
                LengthId,
                LengthName,
                ParameterValue(Length, ValueKind.KLength, "mm"),
                owner_id=SketchValue.id,
            ),
        ),
        (Plane,),
        (SketchValue,),
        (),
        (FeatureValue,),
        (DesignBody(DocumentValue.bodies[0].id, BodyName, FeatureValue.id),),
        metadata={"name": NameValue},
        units=DocumentValue.units,
    )
    AssertValid(PartValue)
    return PartValue

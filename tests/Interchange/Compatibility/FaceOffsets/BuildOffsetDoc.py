from dataclasses import replace as CopyData
from pathlib import Path as FilePath

from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.Records.RecordParameter import Parameter, ParameterValue


# a real native stock supplies the body and topology for public offset schema compatibility checks
def BuildOffsetDoc() -> CadDocument:
    RootPath = FilePath(__file__).resolve().parents[4]
    Document = OpenDocument(
        RootPath / "re/Fusion/Reconstruction/FaceOffsets/Controls/HealthyBefore.f3d"
    )
    if Document.brep is None:
        raise ValueError("Native stock has no physical face topology")
    (BodyValue,) = Document.bodies
    FaceValue = Document.brep.faces[0]
    SelectionValue = Selection(
        "offset-face",
        "offset face",
        (SelectPathElem("body", BodyValue.id), SelectPathElem("face", FaceValue.id)),
    )
    DistanceParam = Parameter(
        "offset-length",
        "offset distance",
        ParameterValue(0.0, ValueKind.KLength, "mm"),
        owner_id="offset-feature",
    )
    Definition = FaceOffset(BodyValue.id, SelectionValue.id, DistanceParam.id)
    Stock = CopyData(Document.feature_timeline[-1], OutputBodyIds=(BodyValue.id,))
    Feature = FeatureStep(
        "offset-feature",
        "Offset",
        FeatureKind.KOffset,
        Stock.order + 1,
        (Stock.id,),
        parameter_ids=(DistanceParam.id,),
        definition=Definition,
        selection_ids=(SelectionValue.id,),
        OutputBodyIds=(BodyValue.id,),
    )
    return CopyData(
        Document,
        parameters=(*Document.parameters, DistanceParam),
        selections=(SelectionValue,),
        feature_timeline=(*Document.feature_timeline[:-1], Stock, Feature),
        bodies=(CopyData(BodyValue, final_feature_id=Feature.id),),
    )

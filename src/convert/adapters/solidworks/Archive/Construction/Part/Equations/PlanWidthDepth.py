from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from interchange.Enums.EnumValues import ParameterRole
from interchange.document.Models.DocumentModel import CadDocument


# this local relation must resolve against the actual anchored rectangle and its evaluated positive blind depth
def PlanWidthDepth(DocumentValue: CadDocument) -> BlindPlan:
    if (
        len(DocumentValue.parameters),
        len(DocumentValue.sketches),
        len(DocumentValue.feature_timeline),
    ) != (3, 1, 1):
        raise ValueError("local equation requires one dimensioned rectangle and boss")
    (SketchValue,) = DocumentValue.sketches
    (FeatureValue,) = DocumentValue.feature_timeline
    if len(SketchValue.parameter_ids) != 2 or len(FeatureValue.parameter_ids) != 1:
        raise ValueError(
            "local equation requires actual width, height and depth owners"
        )
    WidthId, HeightId = SketchValue.parameter_ids
    (DepthId,) = FeatureValue.parameter_ids
    Parameters = {Parameter.id: Parameter for Parameter in DocumentValue.parameters}
    if set(Parameters) != {WidthId, HeightId, DepthId} or len(Parameters) != 3:
        raise ValueError("local equation owners must have distinct parameter IDs")
    DepthValue = Parameters[DepthId]
    ExpressionValue = DepthValue.expression
    if (
        DepthValue.role != ParameterRole.KDerived
        or ExpressionValue is None
        or ExpressionValue.language != "solidworks"
        or ExpressionValue.parameter_ids != (WidthId,)
        or ExpressionValue.source != f'"D1@{SketchValue.name}" / 2'
        or any(
            not NameValue.isascii()
            or not NameValue.isprintable()
            or any(Character in NameValue for Character in ('"', "@", "\\"))
            for NameValue in (SketchValue.name, FeatureValue.name)
        )
    ):
        raise ValueError(
            "local equation must reference the actual width divided by two"
        )
    PlainDepth = ReplaceValue(DepthValue, role=ParameterRole.KDriving, expression=None)
    GeometryDocument = ReplaceValue(
        DocumentValue,
        parameters=tuple(
            PlainDepth if Parameter is DepthValue else Parameter
            for Parameter in DocumentValue.parameters
        ),
    )
    PlanValue = ProjectRectDims(GeometryDocument)
    if (
        DocumentValue.units != "mm"
        or PlanValue.PlaneName != "Front Plane"
        or PlanValue.VerticesValue[0] != (0.0, 0.0)
        or (Parameters[WidthId].name, Parameters[HeightId].name) != ("D1", "D2")
        or Parameters[DepthId].name != "D1"
        or ReadLength(Parameters[WidthId].value) != PlanValue.WidthValue
        or ReadLength(Parameters[HeightId].value) != PlanValue.HeightValue
        or PlanValue.DepthValue != PlanValue.WidthValue / 2.0
    ):
        raise ValueError("local equation disagrees with the anchored Front Plane boss")
    return PlanValue

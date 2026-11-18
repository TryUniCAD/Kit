from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckCircBase import (
    CheckCircBase,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.IsCircDiameter import (
    IsCircDiameter,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircGeom import (
    ReadCircGeom,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    ReadCircParams,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid


# the circle plan projects its actual geometry owners and two editable drivers independent of neutral parameter order
def ProjectCircle(DocumentValue: CadDocument) -> CirclePlan:
    if type(DocumentValue) is not CadDocument:
        raise TypeError("circle boss requires an actual neutral document")
    AssertValid(DocumentValue)
    if (
        len(DocumentValue.parameters),
        len(DocumentValue.sketches),
        len(DocumentValue.feature_timeline),
    ) != (2, 1, 1):
        raise ValueError(
            "circle boss requires one sketch one boss and their two drivers"
        )
    RadialParam, DepthParam = ReadCircParams(DocumentValue)
    Definition = CheckCircBase(DocumentValue, DepthParam)
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral document name"
    )
    UnitScale = {"mm": 0.001, "m": 1.0, "in": 0.0254}.get(DocumentValue.units)
    if not NameValue or UnitScale is None:
        raise ValueError(
            "circle boss requires an explicit document name and supported units"
        )
    SketchValue, FeatureValue = (
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    CircleValue = ReadCircGeom(SketchValue, UnitScale)
    IsDiameter = IsCircDiameter(SketchValue, SketchValue.entities[0].id, RadialParam.id)
    RadiusValue = CircleValue.RadiusValue
    if not IsClose(
        ReadLength(RadialParam.value),
        RadiusValue * (2 if IsDiameter else 1),
        rel_tol=1e-12,
        abs_tol=1e-14,
    ):
        raise ValueError("radial driving length disagrees with the actual circle")
    CenterX, CenterY = CircleValue.CenterValue
    return CirclePlan(
        NameValue,
        DocumentValue.configurations[0].name,
        DocumentValue.support_planes[0].name,
        SketchValue.id,
        SketchValue.name,
        FeatureValue.id,
        FeatureValue.name,
        DepthParam.id,
        DocumentValue.bodies[0].id,
        CircleValue,
        RadialParam.id,
        IsDiameter,
        (CenterX + RadiusValue * 2, CenterY + RadiusValue),
        ReadLength(Definition.length),
    )

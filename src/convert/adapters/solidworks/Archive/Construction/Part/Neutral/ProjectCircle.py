from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import (
    CheckPartLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.IsCircDiameter import (
    IsCircDiameter,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadBossEnd import (
    ReadBossEnd,
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
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrude,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import (
    CheckPartScope,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument


# the circle plan preserves its analytic geometry and actual support and extrusion end ownership
def ProjectCircle(DocumentValue: CadDocument) -> CirclePlan:
    CheckPartScope(DocumentValue, (2, 3))
    PlaneValue = CheckPartLinks(DocumentValue)
    SketchValue, FeatureValue = (
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    AxisValue = ReadPrincAxis(PlaneValue.transform)
    Definition = RequireExtrude(FeatureValue)
    EndValue = ReadBossEnd(Definition, AxisValue)
    RadialParam, DepthParam = ReadCircParams(DocumentValue, Definition)
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral document name"
    )
    UnitScale = {"mm": 0.001, "m": 1.0, "in": 0.0254}.get(DocumentValue.units)
    if not NameValue or UnitScale is None:
        raise ValueError(
            "circle boss requires an explicit document name and supported units"
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
        PlaneValue.name,
        AxisValue,
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
        EndValue,
    )

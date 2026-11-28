from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPlainLinks import (
    CheckPlainLinks,
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
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import (
    RequireBossDef,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import (
    RequirePlainDoc,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument


# the circle graph must retain the actual driver values alongside its geometry and selected support
def ProjectCircle(DocumentValue: CadDocument) -> CirclePlan:
    RequirePlainDoc(DocumentValue, ParameterCount=2)
    PlaneValue, SketchValue, FeatureValue = (
        DocumentValue.support_planes[0],
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    AxisValue = ReadPrincAxis(PlaneValue.transform)
    Definition = RequireBossDef(FeatureValue, AxisValue, AxisValue == "y")
    RadialParam, DepthParam = ReadCircParams(DocumentValue)
    CheckPlainLinks(
        DocumentValue, Definition, DriverValue=DepthParam, AxisValue=AxisValue
    )
    if DocumentValue.units != "mm":
        raise ValueError("ordinary circle preparation requires millimetres")
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral document name"
    )
    CircleValue = ReadCircGeom(SketchValue, 0.001)
    IsDiameter = IsCircDiameter(SketchValue, SketchValue.entities[0].id, RadialParam.id)
    RadiusValue = CircleValue.RadiusValue
    if ReadLength(RadialParam.value) != RadiusValue * (2 if IsDiameter else 1):
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
        ReadLength(Definition.length),
        Definition.reversed,
    )

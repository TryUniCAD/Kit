from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.ReadEllipAxes import (
    ReadEllipAxes,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.ReadEllipGeom import (
    ReadEllipGeom,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPlainLinks import (
    CheckPlainLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
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
from interchange.Enums.EnumUnits import UnitSystem


# real support body configuration and depth links qualify the native ellipse plan before allocation
def ProjectEllipse(DocumentValue: CadDocument) -> EllipsePlan:
    RequirePlainDoc(DocumentValue)
    (FeatureValue,) = DocumentValue.feature_timeline
    (PlaneValue,) = DocumentValue.support_planes
    (SketchValue,) = DocumentValue.sketches
    (ConfigValue,) = DocumentValue.configurations
    Definition = RequireBossDef(FeatureValue)
    CheckPlainLinks(DocumentValue, Definition)
    LengthValue = Definition.length
    if (
        DocumentValue.units != UnitSystem.KMillimeter
        or PlaneValue.name != "Front Plane"
        or ConfigValue.name != "Default"
        or LengthValue is None
        or LengthValue.unit != "mm"
    ):
        raise ValueError(
            "cold ellipse requires the ordinary millimetre Front part and default configuration"
        )
    DepthValue = ReadLength(LengthValue)
    GeometryValue = ReadEllipGeom(SketchValue)
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral document name"
    )
    if not NameValue:
        raise ValueError("cold ellipse requires an authored document name")
    return EllipsePlan(
        NameValue,
        ConfigValue.name,
        PlaneValue.name,
        SketchValue.name,
        FeatureValue.name,
        DepthValue,
        *ReadEllipAxes(GeometryValue, DepthValue),
    )

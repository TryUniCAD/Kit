from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevSelect import (
    ReadRevSelect,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevSense import (
    IsRevReverse,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadThinAngle import (
    ReadThinAngle,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadThinProf import (
    ReadThinProf,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadThinWall import (
    ReadThinWall,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Revolves.ThinRevolve import ThinRevolve


# actual neutral references determine the principal plane axis and active thin dimensions
def ProjectThinRev(
    DocumentValue: CadDocument, AxisValue: str, Definition: ThinRevolve
) -> RevolvePlan:
    FeatureValue = DocumentValue.feature_timeline[0]
    SketchValue = DocumentValue.sketches[0]
    SweepValue = Definition.SweepValue
    AngleValue = ReadThinAngle(DocumentValue, FeatureValue, Definition)
    AxisId = ReadRevSelect(DocumentValue, SweepValue)
    ShapeValue = ReadThinProf(SketchValue, AxisId)
    ReverseValue = IsRevReverse(SweepValue, ShapeValue, PrincipalFrame(AxisValue))
    if ReverseValue:
        raise ValueError("thin revolve currently requires the forward ordered axis")
    RadiusValue = ShapeValue.VerticesValue[0][0] - ShapeValue.AxisStart[0]
    WallValues = ReadThinWall(DocumentValue, FeatureValue, Definition, RadiusValue)
    return RevolvePlan(
        ReadStyleText(DocumentValue.metadata["name"], "neutral document name"),
        DocumentValue.configurations[0].name,
        DocumentValue.support_planes[0].name,
        SketchValue.name,
        FeatureValue.name,
        ShapeValue.VerticesValue,
        ShapeValue.AxisStart,
        ShapeValue.AxisEnd,
        AngleValue,
        ReverseValue,
        SketchValue.id,
        FeatureValue.id,
        SweepValue.AlongParameterId,
        DocumentValue.bodies[0].id,
        SweepValue.AxisSelectionId,
        AxisId,
        (),
        None,
        AxisValue,
        ThinWalls=WallValues,
    )

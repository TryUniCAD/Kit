from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import (
    CheckPartLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectThinRev import (
    ProjectThinRev,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.CheckRevRules import (
    CheckRevRules,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevFeature import (
    ReadRevFeature,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevSelect import (
    ReadRevSelect,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevSense import (
    IsRevReverse,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevShape import (
    ReadRevShape,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RequireRevDoc import (
    RequireRevDoc,
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


# the constructor needs one complete neutral ownership plan before any archive object or native identifier exists
def ProjectRevolve(DocumentValue: CadDocument) -> RevolvePlan:
    RequireRevDoc(DocumentValue)
    PlaneValue = CheckPartLinks(DocumentValue)
    AxisValue = ReadPrincAxis(PlaneValue.transform)
    ThinValue = DocumentValue.feature_timeline[0].definition
    if isinstance(ThinValue, ThinRevolve):
        return ProjectThinRev(DocumentValue, AxisValue, ThinValue)
    Definition, AngleValue, AgainstValue = ReadRevFeature(DocumentValue)
    SketchValue = DocumentValue.sketches[0]
    AxisEntityId = ReadRevSelect(DocumentValue, Definition)
    ShapeValue = ReadRevShape(SketchValue, AxisEntityId)
    UnaryRules, EqualRule = CheckRevRules(SketchValue, ShapeValue)
    ReverseValue = IsRevReverse(Definition, ShapeValue, PrincipalFrame(AxisValue))
    if Definition.SideMode == "symmetric_full" and ReverseValue:
        raise ValueError("mid plane revolve requires its ordered selected axis")
    return RevolvePlan(
        ReadStyleText(DocumentValue.metadata["name"], "neutral document name"),
        DocumentValue.configurations[0].name,
        PlaneValue.name,
        SketchValue.name,
        DocumentValue.feature_timeline[0].name,
        ShapeValue.VerticesValue,
        ShapeValue.AxisStart,
        ShapeValue.AxisEnd,
        AngleValue,
        ReverseValue,
        SketchValue.id,
        DocumentValue.feature_timeline[0].id,
        Definition.AlongParameterId,
        DocumentValue.bodies[0].id,
        DocumentValue.selections[0].id,
        ShapeValue.AxisEntityId,
        UnaryRules,
        EqualRule,
        AxisValue,
        Definition.SideMode,
        AgainstValue,
    )
